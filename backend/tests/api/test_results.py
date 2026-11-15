import asyncio
import json
from typing import Any

import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.consent import Consent
from app.models.person import Person
from tests.api.helpers import INDIA, Stack, bundle_for

pytestmark = pytest.mark.db


async def test_first_sign_in_links_to_the_lab_result(stack: Stack) -> None:
    """V2.3.7."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    response = await stack.http.get("/v1/me/results", headers=headers)
    assert response.status_code == 200
    assert response.json()["has_report"] is True
    assert [fact["gene"] for fact in response.json()["facts"]] == ["HBB"]
    async with stack.factory() as session:
        assert len((await session.scalars(select(Person))).all()) == 1


async def test_signing_in_before_the_result_arrives_links_up_later(stack: Stack) -> None:
    headers = await stack.sign_in("early-login", "fatima")
    assert (await stack.http.get("/v1/me/results", headers=headers)).json()["has_report"] is False
    await stack.ingest(bundle_for("fatima"))
    assert (await stack.http.get("/v1/me/results", headers=headers)).json()["has_report"] is True


async def test_unlinked_user_sees_no_data(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("no-national-id")
    response = await stack.http.get("/v1/me/results", headers=headers)
    assert response.json()["has_report"] is False
    assert response.json()["facts"] == []
    profile = await stack.http.get("/v1/me", headers=headers)
    assert profile.json()["linked_to_national_id"] is False


async def test_no_profile_yet_gets_404(stack: Stack) -> None:
    response = await stack.http.get("/v1/me/results", headers=stack.headers(sub="stranger"))
    assert response.status_code == 404
    assert response.json()["code"] == "profile_not_found"


async def test_national_id_cannot_be_claimed_through_the_request(stack: Stack) -> None:
    """Only a verified token can link an identity. Otherwise anyone could type someone's number."""
    await stack.ingest(bundle_for("fatima"))
    response = await stack.http.post(
        "/v1/me",
        json={"national_id": "784-0000-0000001-1"},
        headers=stack.headers(sub="attacker"),
    )
    assert response.status_code == 422


async def test_an_identity_links_to_only_one_login(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    await stack.sign_in("first-login", "fatima")
    claims = stack.headers(sub="second-login", national_id="784-0000-0000001-1")
    response = await stack.http.post("/v1/me", json={}, headers=claims)
    assert response.status_code == 409
    assert response.json()["code"] == "identity_already_linked"


async def test_provisioning_can_be_repeated(stack: Stack) -> None:
    headers = stack.headers(sub="repeat")
    first = await stack.http.post("/v1/me", json={}, headers=headers)
    second = await stack.http.post("/v1/me", json={}, headers=headers)
    assert first.json()["id"] == second.json()["id"]


async def test_unknown_pack_on_provisioning_is_refused(stack: Stack) -> None:
    response = await stack.http.post(
        "/v1/me", json={"pack_code": "zz-nowhere"}, headers=stack.headers(sub="x")
    )
    assert response.status_code == 422


async def test_id_formatting_does_not_create_a_second_person(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    claims = stack.headers(sub="login", national_id="784000000000011")
    assert (await stack.http.post("/v1/me", json={}, headers=claims)).status_code == 200
    async with stack.factory() as session:
        assert len((await session.scalars(select(Person))).all()) == 1


async def test_results_need_service_consent_first(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = stack.headers(sub="login", national_id="784-0000-0000001-1")
    await stack.http.post("/v1/me", json={}, headers=headers)
    for path in ("/v1/me/results", "/v1/me/risk"):
        response = await stack.http.get(path, headers=headers)
        assert response.status_code == 403
        assert response.json()["code"] == "service_consent_required"
        assert "HBB" not in response.text


async def test_declining_service_consent_is_recorded_as_no(stack: Stack) -> None:
    headers = stack.headers(sub="login")
    await stack.http.post("/v1/me", json={}, headers=headers)
    response = await stack.http.post(
        "/v1/me/service-consent", json={"terms_version": "1", "accepted": False}, headers=headers
    )
    assert response.status_code == 422
    assert (await stack.http.get("/v1/me", headers=headers)).json()["service_consent_at"] is None


async def test_service_consent_goes_in_the_ledger_once(stack: Stack) -> None:
    headers = await stack.sign_in("login")
    await stack.http.post(
        "/v1/me/service-consent", json={"terms_version": "1", "accepted": True}, headers=headers
    )
    async with stack.factory() as session:
        consents = (await session.scalars(select(Consent))).all()
    assert [consent.kind for consent in consents] == ["service"]


async def test_results_are_owner_only(stack: Stack) -> None:
    """V2.5.1. There's no ID to tamper with: each person's token decides whose data they get."""
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    fatima = await stack.sign_in("fatima-login", "fatima")
    stranger = await stack.sign_in("stranger-login")

    own = await stack.http.get("/v1/me/results", headers=fatima)
    other = await stack.http.get("/v1/me/results", headers=stranger)
    assert [fact["gene"] for fact in own.json()["facts"]] == ["HBB"]
    assert other.json()["facts"] == []
    assert "HBB" not in other.text


async def test_response_holds_only_listed_fields(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert set(body) == {
        "has_report",
        "facts",
        "panels",
        "conditions",
        "conditions_exact",
        "pack",
        "withheld",
        "human_contact_required",
    }
    assert set(body["facts"][0]) == {
        "id",
        "scenario",
        "gene",
        "label",
        "percent",
        "one_in",
        "has_number",
        "citation",
    }
    assert "c.20A" not in str(body)


async def test_carrier_gets_no_number_and_no_square(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = (await stack.http.get("/v1/me/risk", headers=headers)).json()
    assert body["facts"][0]["scenario"] == "carrier_self"
    assert body["facts"][0]["percent"] is None
    assert body["visuals"] == []


async def test_x_linked_carrier_gets_her_own_visual(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_carrier"))
    headers = await stack.sign_in("x-login", "x_carrier")
    body = (await stack.http.get("/v1/me/risk", headers=headers)).json()
    assert [visual["type"] for visual in body["visuals"]] == ["x_linked"]
    assert {fact["percent"] for fact in body["facts"]} == {"50"}


async def test_hemizygous_man_is_not_told_he_is_a_carrier(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_man"))
    headers = await stack.sign_in("x-man-login", "x_man")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert [fact["label"] for fact in body["facts"]] == ["possible_affected"]
    assert all(fact["percent"] is None for fact in body["facts"])


async def test_uncertain_finding_shows_no_number_anywhere(stack: Stack) -> None:
    await stack.ingest(bundle_for("uncertain"))
    headers = await stack.sign_in("u-login", "uncertain")
    body = (await stack.http.get("/v1/me/risk", headers=headers)).json()
    assert [fact["has_number"] for fact in body["facts"]] == [False]
    assert body["visuals"] == []


async def test_reading_results_creates_an_audit_row(stack: Stack) -> None:
    """V2.5.5."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    await stack.http.get("/v1/me/results", headers=headers)
    await stack.http.get("/v1/me/risk", headers=headers)
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog).order_by(AuditLog.seq))).all()
        assert (await stack.audit.verify_chain(session)).intact
    actions = [row.action for row in rows]
    assert "results.view" in actions
    assert "risk.view" in actions
    views = [row for row in rows if row.action == "results.view"]
    assert views[0].actor == "fatima-login"


async def test_response_says_how_far_the_country_pack_has_been_reviewed(stack: Stack) -> None:
    await stack.ingest(bundle_for("priya", pack=INDIA), pack=INDIA)
    headers = await stack.sign_in("priya-login", "priya", pack=INDIA)
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["pack"] == {
        "code": INDIA,
        "name": "India",
        "status": "illustrative",
        "reviewed": False,
    }


async def test_language_follows_the_persons_country(stack: Stack) -> None:
    """V2.6.1 at the API. Hindi is offered in the India pack and not in Abu Dhabi."""
    abu_dhabi = await stack.sign_in("ad-login")
    india = await stack.sign_in("in-login", pack=INDIA)
    rejected = await stack.http.patch("/v1/me", json={"preferred_lang": "hi"}, headers=abu_dhabi)
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "invalid_preferred_lang"
    accepted = await stack.http.patch("/v1/me", json={"preferred_lang": "hi"}, headers=india)
    assert accepted.status_code == 200
    assert accepted.json()["preferred_lang"] == "hi"


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"region": "atlantis"}, "invalid_region"),
        ({"age_band": "9-12"}, "invalid_age_band"),
        ({"gender": "nonsense"}, "invalid_gender"),
    ],
)
async def test_equity_groups_must_come_from_the_pack(
    stack: Stack, change: dict[str, Any], code: str
) -> None:
    headers = await stack.sign_in("login")
    response = await stack.http.patch("/v1/me", json=change, headers=headers)
    assert response.status_code == 422
    assert response.json()["code"] == code


async def test_profile_can_be_updated(stack: Stack) -> None:
    headers = await stack.sign_in("login")
    response = await stack.http.patch(
        "/v1/me", json={"region": "al-ain", "literacy_level": "detailed"}, headers=headers
    )
    assert response.json()["region"] == "al-ain"
    assert response.json()["literacy_level"] == "detailed"


async def test_role_cannot_be_set_through_the_profile(stack: Stack) -> None:
    headers = await stack.sign_in("login")
    response = await stack.http.patch("/v1/me", json={"role": "program_admin"}, headers=headers)
    assert response.status_code == 422


async def test_two_tabs_signing_in_together_both_succeed(stack: Stack) -> None:
    headers = stack.headers(sub="two-tabs")
    first, second = await asyncio.gather(
        stack.http.post("/v1/me", json={}, headers=headers),
        stack.http.post("/v1/me", json={}, headers=headers),
    )
    assert (first.status_code, second.status_code) == (200, 200)
    assert first.json()["id"] == second.json()["id"]


async def test_results_name_the_condition_her_exact_change_causes(stack: Stack) -> None:
    """HBB c.20A>T is the sickle cell change. Naming beta thalassaemia too would be wrong for her."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["conditions"] == {"HBB": ["sickle_cell"]}
    assert body["conditions_exact"] == {"HBB": True}


async def test_a_beta_thalassaemia_change_is_named_as_one(stack: Stack) -> None:
    await stack.ingest(bundle_for("khalid"))
    headers = await stack.sign_in("khalid-login", "khalid")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert (body["conditions"], body["conditions_exact"]) == ({"HBB": ["beta_thal"]}, {"HBB": True})


async def test_an_unknown_change_names_every_condition_and_says_it_isnt_exact(
    stack: Stack,
) -> None:
    """A change the pack doesn't list could be either, so neither one is picked."""
    bundle = json.loads(json.dumps(bundle_for("fatima")).replace("c.20A>T", "c.999A>G"))
    await stack.ingest(bundle)
    headers = await stack.sign_in("fatima-login", "fatima")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["conditions"] == {"HBB": ["beta_thal", "sickle_cell"]}
    assert body["conditions_exact"] == {"HBB": False}
    assert "c.999" not in str(body)


async def test_a_gene_outside_the_pack_has_no_conditions_to_name(stack: Stack) -> None:
    await stack.ingest(bundle_for("gene_not_in_pack"))
    headers = await stack.sign_in("g-login", "gene_not_in_pack")
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["conditions"] == {}


async def test_the_country_list_is_public_and_says_what_is_reviewed(stack: Stack) -> None:
    response = await stack.http.get("/v1/packs")
    assert response.status_code == 200
    packs = {pack["code"]: pack for pack in response.json()}
    assert set(packs) == {"ae-abu-dhabi", "in-india"}
    assert packs["in-india"]["languages"] == ["hi", "en"]
    assert all(pack["reviewed"] is False for pack in packs.values())


async def test_a_person_sees_their_own_care_without_reasons_or_priority(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_man"))
    headers = await stack.sign_in("x-login", "x_man")
    response = await stack.http.get("/v1/me/care", headers=headers)
    assert response.status_code == 200
    steps = response.json()
    assert [step["state"] for step in steps] == ["COUNSELLING_REQUESTED"]
    assert set(steps[0]) == {"case_id", "state", "step_due", "with_partner"}
    assert "possibly" not in response.text
    assert "P1" not in response.text


async def test_care_is_private_to_each_person(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_man"))
    await stack.sign_in("x-login", "x_man")
    stranger = await stack.sign_in("stranger")
    assert (await stack.http.get("/v1/me/care", headers=stranger)).json() == []


async def test_care_needs_service_consent(stack: Stack) -> None:
    headers = await stack.provision("no-consent")
    assert (await stack.http.get("/v1/me/care", headers=headers)).status_code == 403
