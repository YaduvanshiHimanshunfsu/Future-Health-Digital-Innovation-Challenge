import asyncio
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select

from app.models.invitation import Invitation
from app.privacy.authz import Authz
from tests.api.helpers import Stack

pytestmark = pytest.mark.db


async def invite(stack: Stack, headers: dict[str, str], **body: Any) -> str:
    response = await stack.http.post(
        "/v1/invitations", json={"relation": "sibling", **body}, headers=headers
    )
    assert response.status_code == 201, response.text
    token: str = response.json()["token"]
    return token


async def test_opening_a_link_many_times_does_not_use_it_up(stack: Stack) -> None:
    """V3.4.1 (H17). WhatsApp and SMS previews open links, so a GET has to change nothing."""
    token = await invite(stack, await stack.sign_in("sender"))
    for _ in range(4):
        assert (await stack.http.get(f"/v1/invitations/{token}")).status_code == 200
    assert (await stack.http.post(f"/v1/invitations/{token}/redeem")).status_code == 200


async def test_reused_expired_and_unknown_links_look_identical(stack: Stack) -> None:
    """V3.4.2."""
    headers = await stack.sign_in("sender")
    reused = await invite(stack, headers)
    await stack.http.post(f"/v1/invitations/{reused}/redeem")
    expired = await invite(stack, headers)
    authz: Authz = stack.app.state.authz
    now = authz.clock()
    authz.clock = lambda: now + timedelta(days=31)

    answers = []
    for token in (reused, expired, "x" * 43, "short"):
        for response in (
            await stack.http.get(f"/v1/invitations/{token}"),
            await stack.http.post(f"/v1/invitations/{token}/redeem"),
        ):
            answers.append(
                (response.status_code, response.json()["code"], response.json()["message"])
            )
    assert len(set(answers)) == 1
    assert answers[0][0] == 404


async def test_only_a_hash_is_stored(stack: Stack) -> None:
    """V3.4.3."""
    token = await invite(stack, await stack.sign_in("sender"))
    async with stack.factory() as session:
        row = await session.scalar(select(Invitation))
    assert row is not None
    assert token not in row.token_hash
    assert row.token_hash != token
    assert b"sibling" not in row.relation_enc


async def test_the_sixth_invite_in_a_day_is_refused(stack: Stack) -> None:
    """V3.4.4."""
    headers = await stack.sign_in("sender")
    for _ in range(5):
        await invite(stack, headers)
    response = await stack.http.post("/v1/invitations", json={"relation": "other"}, headers=headers)
    assert response.status_code == 429
    other = await stack.sign_in("someone-else")
    assert await invite(stack, other)


async def test_nothing_about_the_sender_by_default(stack: Stack) -> None:
    """V3.4.5."""
    headers = await stack.sign_in("sender")
    sender_id = await stack.person_id(headers)
    token = await invite(stack, headers)
    for response in (
        await stack.http.get(f"/v1/invitations/{token}"),
        await stack.http.post(f"/v1/invitations/{token}/redeem"),
    ):
        assert response.json() == {
            "content_key": "invite.generic_screening_info",
            "from_relation": None,
        }
        assert sender_id not in response.text
        assert "sibling" not in response.text


async def test_the_relation_shows_only_if_the_sender_chose_that(stack: Stack) -> None:
    token = await invite(stack, await stack.sign_in("sender"), disclose_identity=True)
    response = await stack.http.get(f"/v1/invitations/{token}")
    assert response.json()["from_relation"] == "sibling"


async def test_two_people_cannot_both_redeem_one_link(stack: Stack) -> None:
    token = await invite(stack, await stack.sign_in("sender"))
    answers = await asyncio.gather(
        *(stack.http.post(f"/v1/invitations/{token}/redeem") for _ in range(4))
    )
    assert sorted(response.status_code for response in answers) == [200, 404, 404, 404]


async def test_public_pages_cannot_be_hammered(stack: Stack) -> None:
    for _ in range(60):
        await stack.http.get("/v1/invitations/" + "x" * 43)
    response = await stack.http.get("/v1/invitations/" + "x" * 43)
    assert response.status_code == 429


async def test_a_link_never_reaches_the_logs(
    stack: Stack, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG")
    token = await invite(stack, await stack.sign_in("sender"))
    await stack.http.get(f"/v1/invitations/{token}")
    await stack.http.post(f"/v1/invitations/{token}/redeem")
    assert token not in caplog.text
    assert token not in " ".join(str(record.__dict__) for record in caplog.records)


async def test_responses_tell_browsers_not_to_keep_the_page(stack: Stack) -> None:
    token = await invite(stack, await stack.sign_in("sender"))
    response = await stack.http.get(f"/v1/invitations/{token}")
    assert response.headers["cache-control"] == "no-store"


async def test_invalid_relation_is_refused(stack: Stack) -> None:
    headers = await stack.sign_in("sender")
    response = await stack.http.post("/v1/invitations", json={"relation": "boss"}, headers=headers)
    assert response.status_code == 422


async def test_inviting_needs_service_consent(stack: Stack) -> None:
    headers = await stack.provision("sender")
    response = await stack.http.post(
        "/v1/invitations", json={"relation": "sibling"}, headers=headers
    )
    assert response.status_code == 403
