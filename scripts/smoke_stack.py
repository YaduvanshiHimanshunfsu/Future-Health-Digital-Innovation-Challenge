"""Checks the running Compose stack end to end, using real tokens and a real database dump.

    cd backend
    uv run python -m synthetic.generate
    uv run python ../scripts/smoke_stack.py

Safe to repeat. Each run posts synthetic reports under new made-up IDs, signs in through the real
browser flow as two temporary users, and removes those users at the end. The synthetic reports stay
in the local database, because the audit trail is append-only. For local stacks only: it reads the
admin password from infra/.env and refuses any other Keycloak address.
"""

import base64
import hashlib
import html
import json
import re
import secrets
import subprocess  # nosec B404 - runs docker with fixed arguments
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "infra" / ".env"
COMPOSE_FILE = ROOT / "infra" / "docker-compose.yml"
PERSONAS = ROOT / "backend" / "synthetic" / "out"
# Server-to-server calls use the address. On Windows, "localhost" tries IPv6 first and adds about 2 s
# to every new connection. Tokens still name localhost as their issuer, because Keycloak's hostname is fixed.
KEYCLOAK = "http://127.0.0.1:8080"
# The browser sign-in page stays on localhost: its cookies and redirects are set for that name.
BROWSER_REALM = "http://localhost:8080/realms/samvid"
# By address: on Windows, "localhost" tries IPv6 first and adds about 2 s to every new connection.
API = "http://127.0.0.1:8000"
REALM = f"{KEYCLOAK}/realms/samvid"
ADMIN_API = f"{KEYCLOAK}/admin/realms/samvid"
REDIRECT = "http://localhost:3000/callback"
ABU_DHABI = "ae-abu-dhabi"
INDIA = "in-india"
# Nothing here may appear in a raw copy of the database.
NEVER_IN_DUMP = (
    "HBB",
    "DMD",
    "CYP21A2",
    "c.20A",
    "784-0000",
    "00-0000-0000",
    "possibly_affected",
    '"sex"',
)


class Results:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, name: str, passed: bool, detail: object = "") -> None:
        suffix = f"  [{detail}]" if detail != "" else ""
        sys.stdout.write(f"{'PASS' if passed else 'FAIL'} {name}{suffix}\n")
        if not passed:
            self.failures.append(name)


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
    return bearer(response.json()["access_token"])


def lab_token(env: dict[str, str]) -> str:
    response = httpx.post(
        f"{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "samvid-lab",
            "client_secret": env["LAB_CLIENT_SECRET"],
        },
    )
    response.raise_for_status()
    token: str = response.json()["access_token"]
    return token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def claims_of(token: str) -> dict[str, Any]:
    part = token.split(".")[1]
    claims: dict[str, Any] = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    return claims


def create_user(admin: dict[str, str], username: str, national_id: str | None) -> tuple[str, str]:
    password = secrets.token_urlsafe(18)
    body: dict[str, Any] = {
        "username": username,
        "enabled": True,
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    }
    if national_id:
        body["attributes"] = {"national_id": [national_id]}
    response = httpx.post(f"{ADMIN_API}/users", json=body, headers=admin)
    response.raise_for_status()
    return response.headers["Location"].rsplit("/", 1)[1], password


def sign_in(username: str, password: str) -> str:
    """Authorisation code with PKCE, the same flow the web app uses."""
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    query = urlencode(
        {
            "client_id": "samvid-web",
            "response_type": "code",
            "scope": "openid",
            "redirect_uri": REDIRECT,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(8),
        }
    )
    with httpx.Client() as client:
        page = client.get(f"{BROWSER_REALM}/protocol/openid-connect/auth?{query}")
        page.raise_for_status()
        # Keycloak's cookies are marked Secure. Browsers treat localhost as secure and Python's
        # cookie jar doesn't, so they're passed on by hand.
        cookies = "; ".join(item.split(";")[0] for item in page.headers.get_list("set-cookie"))
        form = re.search(r'action="([^"]+)"', page.text)
        if form is None:
            raise RuntimeError("no login form in the Keycloak page")
        posted = client.post(
            html.unescape(form.group(1)),
            data={"username": username, "password": password, "credentialId": ""},
            headers={"Cookie": cookies},
        )
        location = posted.headers.get("Location", "")
        if not location.startswith(REDIRECT):
            raise RuntimeError(f"sign-in didn't complete, status {posted.status_code}")
        tokens = client.post(
            f"{REALM}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "samvid-web",
                "code": parse_qs(urlparse(location).query)["code"][0],
                "redirect_uri": REDIRECT,
                "code_verifier": verifier,
            },
        )
        tokens.raise_for_status()
        token: str = tokens.json()["access_token"]
        return token


def persona_bundle(pack: str, slug: str, run: str) -> tuple[dict[str, Any], str]:
    """A persona under a new report ID and national ID, so runs don't collide on a linked identity."""
    path = PERSONAS / pack / "personas" / f"{slug}.json"
    bundle: dict[str, Any] = json.loads(path.read_text("utf-8"))
    serial = secrets.randbelow(10_000_000)
    new_id = (
        f"784-0000-{serial:07d}-9" if pack == ABU_DHABI else f"00-0000-{serial % 10_000:04d}-9999"
    )
    bundle["entry"][0]["resource"]["identifier"][0]["value"] = new_id
    bundle["entry"][1]["resource"]["identifier"][0]["value"] = f"SMOKE-{run}-{slug}"
    return bundle, new_id


def ingest(token: str, bundle: Any, pack: str = ABU_DHABI) -> httpx.Response:
    return httpx.post(
        f"{API}/v1/reports:ingest",
        json=bundle,
        headers={**bearer(token), "X-Country-Pack": pack},
    )


def in_postgres(*command: str) -> str:
    return compose("exec", "-T", "postgres", *command)


def check_ingestion(results: Results, lab: str, run: str) -> str:
    bundle, national_id = persona_bundle(ABU_DHABI, "fatima", run)
    first = ingest(lab, bundle)
    results.check("a lab token posts a report", first.status_code == 201, first.status_code)
    replay = ingest(lab, bundle)
    same = replay.status_code == 200 and replay.json()["report_id"] == first.json()["report_id"]
    results.check("a replay returns the same report", same)
    for pack, slug in (
        (ABU_DHABI, "x_man"),
        (ABU_DHABI, "x_carrier"),
        (ABU_DHABI, "uncertain"),
        (INDIA, "priya"),
    ):
        other, _ = persona_bundle(pack, slug, run)
        response = ingest(lab, other, pack)
        results.check(f"ingest {slug} ({pack})", response.status_code == 201, response.status_code)
    empty = {"resourceType": "Bundle", "type": "collection", "entry": []}
    results.check("a malformed bundle gets 422", ingest(lab, empty).status_code == 422)
    no_token = httpx.post(f"{API}/v1/reports:ingest", json={})
    results.check("ingest with no token gets 401", no_token.status_code == 401)
    return national_id


def check_owner(results: Results, token: str, national_id: str) -> None:
    headers = bearer(token)
    claims = claims_of(token)
    results.check("the token carries the national ID", claims.get("national_id") == national_id)
    audience = claims["aud"] if isinstance(claims["aud"], list) else [claims["aud"]]
    results.check("the token's audience includes the API", "samvid-api" in audience)
    results.check("a person's token can't ingest", ingest(token, {}).status_code == 403)
    missing = httpx.get(f"{API}/v1/me/results", headers=headers)
    results.check("no profile yet gets 404", missing.status_code == 404)

    linked = httpx.post(f"{API}/v1/me", json={}, headers=headers)
    is_linked = linked.status_code == 200 and linked.json()["linked_to_national_id"] is True
    results.check("first sign-in links to the lab result", is_linked)
    blocked = httpx.get(f"{API}/v1/me/results", headers=headers)
    results.check(
        "results wait for service consent", blocked.status_code == 403 and "HBB" not in blocked.text
    )
    agreed = httpx.post(
        f"{API}/v1/me/service-consent",
        json={"terms_version": "1", "accepted": True},
        headers=headers,
    )
    results.check("service consent recorded", agreed.status_code == 200)

    response = httpx.get(f"{API}/v1/me/results", headers=headers)
    body = response.json()
    genes = [fact["gene"] for fact in body["facts"]]
    results.check("the owner reads their own result", body["has_report"] and genes == ["HBB"])
    results.check("a carrier fact has no number", body["facts"][0]["percent"] is None)
    results.check("the response omits the variant", "c.20A" not in response.text)
    results.check("the response says the pack is unreviewed", body["pack"]["reviewed"] is False)
    risk = httpx.get(f"{API}/v1/me/risk", headers=headers)
    results.check("a single carrier sees no square", risk.json()["visuals"] == [])


def check_id_lock(
    results: Results, env: dict[str, str], user_id: str, username: str, password: str, target: str
) -> None:
    """Nobody can give themselves another person's national ID through their own account."""
    headers = {**bearer(sign_in(username, password)), "Accept": "application/json"}
    profile = httpx.get(f"{BROWSER_REALM}/account/", headers=headers)
    results.check("the user can't see the field", "national_id" not in profile.text)
    changed = {**profile.json(), "firstName": "Changed"}
    plain = httpx.post(f"{BROWSER_REALM}/account/", headers=headers, json=changed)
    # Proves the refusal below is about the field, and not just a badly formed request.
    results.check("an ordinary profile edit works", plain.status_code == 204, plain.status_code)
    attempt = httpx.post(
        f"{BROWSER_REALM}/account/",
        headers=headers,
        json={**changed, "attributes": {"national_id": [target]}},
    )
    results.check(
        "setting the national ID is refused as read-only",
        attempt.status_code == 400 and "read-only" in attempt.text,
    )
    stored = httpx.get(f"{ADMIN_API}/users/{user_id}", headers=admin_headers(env)).json()
    results.check("the national ID stayed unset", "national_id" not in stored.get("attributes", {}))


def check_stranger(results: Results, token: str, target: str) -> None:
    headers = bearer(token)
    results.check("a fresh token has no national ID", "national_id" not in claims_of(token))
    claimed = httpx.post(f"{API}/v1/me", json={"national_id": target}, headers=headers)
    results.check("a national ID in the request is refused", claimed.status_code == 422)
    profile = httpx.post(f"{API}/v1/me", json={}, headers=headers)
    results.check("the stranger's profile is unlinked", not profile.json()["linked_to_national_id"])
    httpx.post(
        f"{API}/v1/me/service-consent",
        json={"terms_version": "1", "accepted": True},
        headers=headers,
    )
    response = httpx.get(f"{API}/v1/me/results", headers=headers)
    body = response.json()
    results.check(
        "the stranger sees nobody's data",
        body["facts"] == [] and body["has_report"] is False and "HBB" not in response.text,
    )


def check_database(results: Results) -> None:
    dump = in_postgres("pg_dump", "-U", "postgres", "--data-only", "--inserts", "samvid")
    results.check("the dump holds findings", "INSERT INTO public.carrier_finding" in dump)
    # pg_dump writes binary columns as hex, so a plain search would pass even with no encryption.
    binary = re.findall(r"'\\x([0-9a-f]+)'", dump)
    results.check("the dump holds binary columns to inspect", len(binary) > 0, len(binary))
    readable = "\n".join([dump, *(bytes.fromhex(v).decode("utf-8", "replace") for v in binary)])
    for secret in NEVER_IN_DUMP:
        results.check(f"the raw dump holds no {secret!r}", secret not in readable)

    def query(sql: str) -> str:
        return in_postgres("psql", "-U", "postgres", "-d", "samvid", "-At", "-c", sql)

    cases = query("select priority, state from care_case")
    results.check("a P1 case opened at ingest, with no chat", "P1|COUNSELLING_REQUESTED" in cases)
    actions = query("select distinct action from audit_log")
    for action in ("report.ingest", "results.view", "risk.view"):
        results.check(f"the audit trail has {action}", action in actions)


def compose(*command: str) -> str:
    base = ["docker", "compose", "--env-file", str(ENV_FILE), "-f", str(COMPOSE_FILE)]
    done = subprocess.run(  # noqa: S603 - fixed arguments, local stack only  # nosec B603
        [*base, *command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return done.stdout


def onboard(
    env: dict[str, str], created: list[str], username: str, national_id: str | None = None
) -> dict[str, str]:
    # A fresh admin token each time, since they only last a minute.
    user_id, password = create_user(admin_headers(env), username, national_id)
    created.append(user_id)
    headers = bearer(sign_in(username, password))
    httpx.post(f"{API}/v1/me", json={}, headers=headers).raise_for_status()
    httpx.post(
        f"{API}/v1/me/service-consent",
        json={"terms_version": "1", "accepted": True},
        headers=headers,
    ).raise_for_status()
    return headers


def check_couple(
    results: Results, env: dict[str, str], created: list[str], lab: str, run: str
) -> None:
    first_bundle, first_id = persona_bundle(ABU_DHABI, "fatima", f"{run}-c1")
    second_bundle, second_id = persona_bundle(ABU_DHABI, "khalid", f"{run}-c2")
    ingest(lab, first_bundle).raise_for_status()
    ingest(lab, second_bundle).raise_for_status()
    first = onboard(env, created, f"smoke-first-{run}", first_id)
    second = onboard(env, created, f"smoke-second-{run}", second_id)
    stranger = onboard(env, created, f"smoke-outsider-{run}")

    couple = httpx.post(f"{API}/v1/couples", json={}, headers=first).json()
    couple_url = f"{API}/v1/couples/{couple['id']}"
    joined = httpx.post(
        f"{API}/v1/couples/join", json={"invite_code": couple["invite_code"]}, headers=second
    )
    results.check("a partner joins with the invite code", joined.status_code == 200)
    agreement = {
        "reveal_level": "yes_no",
        "terms_version": "1",
        "understood_what_a_result_reveals": True,
    }
    early = httpx.post(f"{couple_url}/match", headers=first)
    results.check("no match before both agree", early.status_code == 409, early.status_code)
    for headers in (first, second):
        httpx.post(f"{couple_url}/consent", json=agreement, headers=headers).raise_for_status()

    match = httpx.post(f"{couple_url}/match", headers=first)
    body = match.json()
    results.check("a known at-risk couple gets shared", body.get("outcome") == "shared")
    results.check("yes-or-no shows no gene name", "HBB" not in match.text)
    gene_list = httpx.post(f"{couple_url}/match", json={"genes": ["HBB"]}, headers=first)
    results.check("a gene list in the request is refused", gene_list.status_code == 422)
    follow_up = httpx.get(couple_url, headers=second).json()["follow_up"]
    results.check("the other partner sees a follow-up", follow_up is not None)
    outsider = httpx.post(f"{couple_url}/match", headers=stranger)
    results.check("an outsider gets 404", outsider.status_code == 404)

    httpx.delete(f"{couple_url}/consent", headers=second).raise_for_status()
    withdrawn = httpx.post(f"{couple_url}/match", headers=first)
    results.check("withdrawing blocks the next match", withdrawn.status_code == 409)


def grant_share(owner: dict[str, str], grantee: dict[str, str]) -> dict[str, Any]:
    code = httpx.post(f"{API}/v1/consents/receive-code", headers=grantee).json()["code"]
    response = httpx.post(
        f"{API}/v1/consents",
        json={
            "grantee_code": code,
            "kind": "share_full",
            "purpose": "family_support",
            "terms_version": "1",
            "duration_days": 7,
        },
        headers=owner,
    )
    response.raise_for_status()
    granted: dict[str, Any] = response.json()
    return granted


def check_sharing(
    results: Results, env: dict[str, str], created: list[str], lab: str, run: str
) -> None:
    bundle, national_id = persona_bundle(ABU_DHABI, "fatima", f"{run}-s")
    ingest(lab, bundle).raise_for_status()
    owner = onboard(env, created, f"smoke-sharer-{run}", national_id)
    grantee = onboard(env, created, f"smoke-grantee-{run}")

    share = grant_share(owner, grantee)
    url = f"{API}/v1/shared/{share['id']}"
    results.check("a share is ready straight away", share["access_ready"] is True)
    results.check("the grantee reads it", httpx.get(url, headers=grantee).status_code == 200)
    started = time.perf_counter()
    revoked = httpx.delete(f"{API}/v1/consents/{share['id']}", headers=owner)
    elapsed = time.perf_counter() - started
    results.check(
        "revoking takes under 1 s", revoked.status_code == 204 and elapsed < 1, f"{elapsed:.3f}s"
    )
    results.check(
        "after revoke the grantee gets 404", httpx.get(url, headers=grantee).status_code == 404
    )

    # With the real service stopped.
    standing = grant_share(owner, grantee)
    standing_url = f"{API}/v1/shared/{standing['id']}"
    compose("stop", "openfga")
    try:
        denied = httpx.get(standing_url, headers=grantee, timeout=10)
        results.check(
            "with OpenFGA stopped, reads are denied", denied.status_code == 404, denied.status_code
        )
        refused = httpx.delete(f"{API}/v1/consents/{standing['id']}", headers=owner, timeout=10)
        results.check(
            "with OpenFGA stopped, revoke says 503", refused.status_code == 503, refused.status_code
        )
        listing = httpx.get(f"{API}/v1/consents", headers=owner).json()["given"]
        entry = next(item for item in listing if item["id"] == standing["id"])
        results.check("and the consent stays visibly active", entry["active"] is True)
        pending = grant_share(owner, grantee)
        results.check("a share made now isn't ready", pending["access_ready"] is False)
    finally:
        compose("up", "-d", "--wait", "openfga")

    # The API isn't involved from here: only the worker and its schedule can finish this.
    deadline = time.monotonic() + 90
    pending_url = f"{API}/v1/shared/{pending['id']}"
    status = 0
    while time.monotonic() < deadline:
        status = httpx.get(pending_url, headers=grantee).status_code
        if status == 200:
            break
        time.sleep(3)
    results.check("the background worker applies it after the outage", status == 200, status)
    finished = httpx.delete(f"{API}/v1/consents/{standing['id']}", headers=owner)
    results.check("the revoke works once it's back", finished.status_code == 204)


def check_invitations(results: Results, env: dict[str, str], created: list[str], run: str) -> None:
    sender = onboard(env, created, f"smoke-sender-{run}")
    created_invite = httpx.post(
        f"{API}/v1/invitations", json={"relation": "sibling"}, headers=sender
    )
    token = created_invite.json()["token"]
    url = f"{API}/v1/invitations/{token}"
    views = [httpx.get(url).status_code for _ in range(3)]
    results.check("a link preview doesn't use up an invitation", views == [200, 200, 200], views)
    page = httpx.get(url).json()
    results.check("the page names nobody", page["from_relation"] is None)
    results.check("redeeming works once", httpx.post(f"{url}/redeem").status_code == 200)
    again = httpx.post(f"{url}/redeem")
    unknown = httpx.post(f"{API}/v1/invitations/{'x' * 43}/redeem")
    same = (again.status_code, again.json()["code"]) == (
        unknown.status_code,
        unknown.json()["code"],
    )
    results.check("a used link looks like an unknown one", same)
    results.check("the link isn't in the API's logs", token not in compose("logs", "api"))


def main() -> int:
    if not (PERSONAS / ABU_DHABI / "personas" / "fatima.json").exists():
        sys.stderr.write("Run `uv run python -m synthetic.generate` in backend/ first.\n")
        return 2
    env = read_env()
    results = Results()
    run = secrets.token_hex(3)
    admin = admin_headers(env)
    created: list[str] = []
    try:
        national_id = check_ingestion(results, lab_token(env), run)

        owner = f"smoke-owner-{run}"
        owner_id, owner_password = create_user(admin, owner, national_id)
        created.append(owner_id)
        check_owner(results, sign_in(owner, owner_password), national_id)

        stranger = f"smoke-stranger-{run}"
        stranger_id, stranger_password = create_user(admin, stranger, None)
        created.append(stranger_id)
        check_id_lock(results, env, stranger_id, stranger, stranger_password, national_id)
        check_stranger(results, sign_in(stranger, stranger_password), national_id)

        lab = lab_token(env)
        check_couple(results, env, created, lab, run)
        check_sharing(results, env, created, lab, run)
        check_invitations(results, env, created, run)
        check_database(results)
    finally:
        fresh = admin_headers(env)
        for user_id in created:
            httpx.delete(f"{ADMIN_API}/users/{user_id}", headers=fresh)
        sys.stdout.write(f"Removed {len(created)} temporary users.\n")

    summary = f"FAILED: {results.failures}" if results.failures else "All checks passed."
    sys.stdout.write(summary + "\n")
    return 1 if results.failures else 0


if __name__ == "__main__":
    sys.exit(main())
