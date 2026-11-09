"""Creates demo accounts and synthetic lab reports on the running local stack.

    cd backend
    uv run python -m synthetic.generate
    uv run python ../scripts/seed_demo.py

Safe to repeat. Every person is fictional, and every report is labelled as test data. For local
stacks only: it reads the admin password from infra/.env, and there's one shared demo password, in
that file, as DEMO_PASSWORD.
"""

import json
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "infra" / ".env"
PERSONAS = ROOT / "backend" / "synthetic" / "out"
# Server-to-server calls use the address. On Windows, "localhost" tries IPv6 first and adds about 2 s
# to every new connection. Tokens still name localhost as their issuer, because Keycloak's hostname is fixed.
KEYCLOAK = "http://127.0.0.1:8080"
# By address: on Windows, "localhost" tries IPv6 first and adds about 2 s to every new connection.
API = "http://127.0.0.1:8000"
ADMIN_API = f"{KEYCLOAK}/admin/realms/samvid"
ABU_DHABI, INDIA = "ae-abu-dhabi", "in-india"

# Username, the persona whose report they own, its country pack, and their role.
PEOPLE = [
    ("demo-fatima", "fatima", ABU_DHABI, "individual"),
    ("demo-khalid", "khalid", ABU_DHABI, "individual"),
    ("demo-x-carrier", "x_carrier", ABU_DHABI, "individual"),
    ("demo-x-man", "x_man", ABU_DHABI, "individual"),
    ("demo-uncertain", "uncertain", ABU_DHABI, "individual"),
    ("demo-no-findings", "no_findings", ABU_DHABI, "individual"),
    ("demo-priya", "priya", INDIA, "individual"),
    ("demo-rohan", "rohan", INDIA, "individual"),
    ("demo-no-report", None, ABU_DHABI, "individual"),
    ("demo-counsellor", None, ABU_DHABI, "counsellor"),
    ("demo-doctor", None, ABU_DHABI, "physician"),
    ("demo-auditor", None, ABU_DHABI, "auditor"),
    ("demo-coordinator", None, ABU_DHABI, "program_admin"),
]


def read_env() -> dict[str, str]:
    lines = ENV_FILE.read_text("utf-8").splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def admin_headers(env: dict[str, str]) -> dict[str, str]:
    response = httpx.post(
        f"{KEYCLOAK}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": env["KEYCLOAK_ADMIN_PASSWORD"],
        },
    )
    response.raise_for_status()
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def persona(pack: str, slug: str) -> dict[str, Any]:
    path = PERSONAS / pack / "personas" / f"{slug}.json"
    loaded: dict[str, Any] = json.loads(path.read_text("utf-8"))
    return loaded


def national_id_of(bundle: dict[str, Any]) -> str:
    value: str = bundle["entry"][0]["resource"]["identifier"][0]["value"]
    return value


def post_report(env: dict[str, str], bundle: dict[str, Any], pack: str) -> None:
    token = httpx.post(
        f"{KEYCLOAK}/realms/samvid/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "samvid-lab",
            "client_secret": env["LAB_CLIENT_SECRET"],
        },
    )
    token.raise_for_status()
    response = httpx.post(
        f"{API}/v1/reports:ingest",
        json=bundle,
        headers={
            "Authorization": "Bearer " + token.json()["access_token"],
            "X-Country-Pack": pack,
        },
    )
    # A conflict means this demo report is already on file from an earlier run, which is fine.
    if response.status_code == HTTPStatus.CONFLICT:
        return
    response.raise_for_status()


def upsert_user(env: dict[str, str], username: str, national_id: str | None, role: str) -> None:
    admin = admin_headers(env)
    body: dict[str, Any] = {
        "username": username,
        "enabled": True,
        "attributes": {"national_id": [national_id]} if national_id else {},
        "credentials": [{"type": "password", "value": env["DEMO_PASSWORD"], "temporary": False}],
    }
    created = httpx.post(f"{ADMIN_API}/users", json=body, headers=admin)
    if created.status_code == HTTPStatus.CONFLICT:
        found = httpx.get(
            f"{ADMIN_API}/users", params={"username": username, "exact": "true"}, headers=admin
        ).json()
        user_id = found[0]["id"]
        httpx.put(f"{ADMIN_API}/users/{user_id}", json=body, headers=admin).raise_for_status()
    else:
        created.raise_for_status()
        user_id = created.headers["Location"].rsplit("/", 1)[1]
    role_body = httpx.get(f"{ADMIN_API}/roles/{role}", headers=admin)
    role_body.raise_for_status()
    httpx.post(
        f"{ADMIN_API}/users/{user_id}/role-mappings/realm",
        json=[role_body.json()],
        headers=admin,
    ).raise_for_status()


def main() -> int:
    if not (PERSONAS / ABU_DHABI / "personas" / "fatima.json").exists():
        sys.stderr.write("Run `uv run python -m synthetic.generate` in backend/ first.\n")
        return 2
    env = read_env()
    for username, slug, pack, role in PEOPLE:
        national_id: str | None = None
        if slug is not None:
            bundle = persona(pack, slug)
            post_report(env, bundle, pack)
            national_id = national_id_of(bundle)
        upsert_user(env, username, national_id, role)
        sys.stdout.write(f"{username:18} {role:11} {pack:13} {slug or '-'}\n")
    sys.stdout.write("\nPassword for all of them: DEMO_PASSWORD in infra/.env\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
