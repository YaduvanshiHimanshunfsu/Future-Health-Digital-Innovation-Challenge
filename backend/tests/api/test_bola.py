import re

import pytest

from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db

# Public by design. Everything else needs a token.
PUBLIC = {
    "/v1/health",
    "/v1/ready",
    "/v1/packs",
    # Recipients of an invitation have no account. Tests in test_invitations.py cover these.
    "/v1/invitations/{token}",
    "/v1/invitations/{token}/redeem",
    # Finding a centre needs no account (V5.2.6).
    "/v1/centres",
}
EXPECTED = {
    "/v1/reports:ingest",
    "/v1/me",
    "/v1/me/service-consent",
    "/v1/me/results",
    "/v1/me/risk",
    "/v1/me/access-log",
    "/v1/me/care",
    "/v1/me/results-preference",
    "/v1/consents",
    "/v1/consents/{consent_id}",
    "/v1/consents/receive-code",
    "/v1/shared/{consent_id}",
    "/v1/couples",
    "/v1/couples/join",
    "/v1/couples/{couple_id}",
    "/v1/couples/{couple_id}/consent",
    "/v1/couples/{couple_id}/match",
    "/v1/invitations",
    "/v1/cases/{case_id}",
    "/v1/cases/{case_id}/break-glass",
    "/v1/break-glass",
    "/v1/break-glass/{event_id}/review",
    "/v1/chat",
    "/v1/options",
    "/v1/values",
    "/v1/values/{note_id}/share",
    "/v1/cases",
    "/v1/cases/{case_id}/claim",
    "/v1/cases/{case_id}/assign",
    "/v1/me/journey",
    "/v1/me/reminders",
    "/v1/journey/{case_id}/steps",
    "/v1/cases/{case_id}/advance",
    "/v1/booking/slots",
    "/v1/booking/slots/{slot_id}/book",
    "/v1/booking/mine",
    "/v1/booking/schedule",
    "/v1/booking/appointments/{appointment_id}/cancel",
    "/v1/booking/appointments/{appointment_id}/complete",
    "/v1/cases/{case_id}/referrals",
    "/v1/referrals/{referral_id}/send",
    "/v1/referrals/{referral_id}/accept",
    "/v1/referrals/{referral_id}/cancel",
    "/v1/assessments/mine",
    "/v1/assessments/{instrument}",
    "/v1/analytics/overview",
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
ANY_ID = "00000000-0000-0000-0000-000000000000"


def api_paths(stack: Stack) -> dict[str, dict[str, object]]:
    # The published schema, because FastAPI's internal route objects change between versions.
    paths: dict[str, dict[str, object]] = stack.app.openapi()["paths"]
    return paths


async def test_every_route_needs_a_token(stack: Stack) -> None:
    """Covers the whole API, so a route added later without auth fails here."""
    paths = api_paths(stack)
    assert set(paths) >= EXPECTED, "the walk has to reach the routes it claims to check"
    for path, operations in paths.items():
        if path in PUBLIC:
            continue
        url = re.sub(r"{[^}]+}", ANY_ID, path)
        for method in set(operations) & HTTP_METHODS:
            response = await stack.http.request(method, url)
            assert response.status_code == 401, f"{method} {path}"


async def test_no_personal_route_takes_a_person_id(stack: Stack) -> None:
    """V2.5.1: a person's data can't be reached by changing an ID, because none is accepted."""
    personal = [path for path in api_paths(stack) if path.startswith("/v1/me")]
    assert len(personal) >= 4
    assert [path for path in personal if "{" in path] == []


async def test_a_token_with_no_profile_gets_404_and_nobody_elses_data(stack: Stack) -> None:
    """V2.5.1. The nearest thing to "user B asks for A's data" on routes with no ID in them."""
    await stack.ingest(bundle_for("fatima"))
    response = await stack.http.get("/v1/me/results", headers=stack.headers(sub="user-b"))
    assert response.status_code == 404
    assert "HBB" not in response.text
