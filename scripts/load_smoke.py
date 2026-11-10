"""A small load check on the real stack (Phase 6.3, V6.3.4): p95 under 300 ms for non-AI routes.

    cd backend && uv run python ../scripts/load_smoke.py               # from inside the Docker network
    cd backend && uv run python ../scripts/load_smoke.py --from-host   # through the published port

By default the requests come from inside the Docker network (the worker container), because on
Windows, Docker Desktop's port forwarding becomes the bottleneck long before the API does: measured
on 10 Nov, the same load gave p95 482 ms through the forwarded port and 38 ms from inside the
network, with one API process or four. A real deployment has no such proxy. `--from-host` keeps the
other measurement available, and the output says which one it is.

One temporary person is created in Keycloak, given a synthetic report, used for the run, and deleted
afterwards whatever happens. The token reaches the container through an environment variable, never
the command line. Chat isn't measured: it waits on a model by design. This is a smoke test on one
laptop, not a capacity claim.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess  # nosec B404 - runs docker with fixed arguments
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_stack import (  # noqa: E402
    ABU_DHABI,
    ADMIN_API,
    API,
    COMPOSE_FILE,
    admin_headers,
    bearer,
    create_user,
    ingest,
    lab_token,
    persona_bundle,
    read_env,
    sign_in,
)

TARGET_P95_MS = 300.0
PUBLIC = ["/v1/health", "/v1/packs", "/v1/centres"]
SIGNED_IN = [
    "/v1/me",
    "/v1/me/results",
    "/v1/me/risk",
    "/v1/me/journey",
    "/v1/me/care",
    "/v1/consents",
    "/v1/options",
]

# Runs wherever the load comes from. Prints one JSON line: timings per route and any errors.
PROBE = """
import asyncio, json, os, statistics, time, httpx
BASE, TOKEN = os.environ["LOAD_BASE"], os.environ["LOAD_TOKEN"]
PUBLIC, SIGNED = json.loads(os.environ["LOAD_PUBLIC"]), json.loads(os.environ["LOAD_SIGNED"])
REQUESTS, CONCURRENCY = int(os.environ["LOAD_REQUESTS"]), int(os.environ["LOAD_CONCURRENCY"])
async def main():
    paths, timings, errors = PUBLIC + SIGNED, {}, []
    auth = {"Authorization": "Bearer " + TOKEN}
    gate = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(timeout=10) as http:
        for path in paths:
            await http.get(BASE + path, headers=auth if path in SIGNED else {})
        async def one(i):
            path = paths[i % len(paths)]
            async with gate:
                start = time.perf_counter()
                r = await http.get(BASE + path, headers=auth if path in SIGNED else {})
                timings.setdefault(path, []).append((time.perf_counter() - start) * 1000)
                if r.status_code != 200:
                    errors.append(path + " " + str(r.status_code))
        start = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(REQUESTS)))
        elapsed = time.perf_counter() - start
    print(json.dumps({"timings": timings, "errors": errors, "elapsed": elapsed}))
asyncio.run(main())
"""


def report(data: dict[str, object], requests: int, concurrency: int, where: str) -> int:
    import statistics

    timings: dict[str, list[float]] = data["timings"]  # type: ignore[assignment]
    errors: list[str] = data["errors"]  # type: ignore[assignment]
    elapsed = float(data["elapsed"])  # type: ignore[arg-type]
    every = sorted(t for values in timings.values() for t in values)
    p95 = statistics.quantiles(every, n=20)[-1]
    sys.stdout.write(
        f"{requests} requests, {concurrency} at a time, {requests / elapsed:.0f} per second, {where}\n"
    )
    sys.stdout.write(f"{'route':<20} {'n':>4} {'p50 ms':>8} {'p95 ms':>8}\n")
    for path, values in sorted(timings.items()):
        q = statistics.quantiles(values, n=20) if len(values) > 1 else values * 19
        sys.stdout.write(
            f"{path:<20} {len(values):>4} {statistics.median(values):>8.1f} {q[-1]:>8.1f}\n"
        )
    sys.stdout.write(
        f"All routes: p95 {p95:.1f} ms against a target of {TARGET_P95_MS:.0f} ms. Errors: {len(errors)}\n"
    )
    return 0 if p95 < TARGET_P95_MS and not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--from-host", action="store_true", help="through the published port")
    args = parser.parse_args()
    env = read_env()
    run_id = secrets.token_hex(3)
    bundle, national_id = persona_bundle(ABU_DHABI, "fatima", run_id)
    user_id, password = create_user(admin_headers(env), f"load-{run_id}", national_id)
    try:
        ingest(lab_token(env), bundle)
        headers = bearer(sign_in(f"load-{run_id}", password))
        httpx.post(f"{API}/v1/me", json={}, headers=headers)
        httpx.post(
            f"{API}/v1/me/service-consent",
            json={"terms_version": "1", "accepted": True},
            headers=headers,
        )
        probe_env = {
            **os.environ,
            "LOAD_TOKEN": headers["Authorization"].removeprefix("Bearer "),
            "LOAD_PUBLIC": json.dumps(PUBLIC),
            "LOAD_SIGNED": json.dumps(SIGNED_IN),
            "LOAD_REQUESTS": str(args.requests),
            "LOAD_CONCURRENCY": str(args.concurrency),
        }
        if args.from_host:
            probe_env["LOAD_BASE"] = API
            command = [sys.executable, "-c", PROBE]
            where = "from the host, through Docker's forwarded port"
        else:
            probe_env["LOAD_BASE"] = "http://api:8000"
            command = [
                "docker", "compose", "-f", str(COMPOSE_FILE), "exec", "-T",
                "-e", "LOAD_BASE", "-e", "LOAD_TOKEN", "-e", "LOAD_PUBLIC", "-e", "LOAD_SIGNED",
                "-e", "LOAD_REQUESTS", "-e", "LOAD_CONCURRENCY",
                "worker", "python", "-c", PROBE,
            ]  # fmt: skip
            where = "from inside the Docker network"
        done = subprocess.run(  # noqa: S603  # nosec B603 - fixed arguments
            command, env=probe_env, capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            sys.stderr.write(done.stderr[-2000:])
            return 2
        return report(
            json.loads(done.stdout.strip().splitlines()[-1]), args.requests, args.concurrency, where
        )
    finally:
        httpx.delete(f"{ADMIN_API}/users/{user_id}", headers=admin_headers(env))


if __name__ == "__main__":
    sys.exit(main())
