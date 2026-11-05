import uuid
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.models.audit import AuditLog
from app.models.case import CareCase
from app.privacy.authz import Authz, RelationTuple
from app.privacy.matching import MatchOutcome, _outcome, effective_relationship, effective_reveal
from app.privacy.redaction import build_llm_facts
from app.risk_engine.engine import couple_assessment, partner_view
from app.risk_engine.types import (
    Classification,
    Finding,
    PartnerRecord,
    Relationship,
    Reveal,
    Sex,
    Viewer,
    Zygosity,
)
from synthetic.generate import SyntheticPerson, build_bundle
from tests.api.helpers import INDIA, Stack, bundle_for

pytestmark = pytest.mark.db


def finding(gene: str) -> Finding:
    return Finding(gene, Classification.PATHOGENIC, Zygosity.HETEROZYGOUS, "c.1A>G")


async def run(stack: Stack, couple_id: str, headers: dict[str, str]) -> Any:
    response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def test_a_known_at_risk_couple_gets_shared(stack: Stack) -> None:
    """V3.3.1. The original spec answered "no shared finding" here, every time (C1)."""
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid")
    body = await run(stack, couple_id, first)
    assert body["outcome"] == "shared"
    assert {fact["percent"] for fact in body["facts"]} == {"25", "50"}


async def test_a_partner_with_no_report_cannot_read_as_none(stack: Stack) -> None:
    """V3.3.2 (C2)."""
    await stack.ingest(bundle_for("fatima"))
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("untested-login")
    couple_id = await stack.link_couple(first, second)
    await stack.agree_to_match(couple_id, first)
    await stack.agree_to_match(couple_id, second)
    body = await run(stack, couple_id, first)
    assert body["outcome"] == "cannot_determine"
    assert body["facts"] == []
    assert "isn't a negative" in body["notice"]


async def test_untrusted_reports_cannot_produce_a_result(make_stack: Any) -> None:
    """Both partners have findings, but neither report is trusted, so "none" would be false."""
    stack = await make_stack(lab_attestation="unverified")
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid")
    assert (await run(stack, couple_id, first))["outcome"] == "cannot_determine"


async def test_none_shared_never_claims_no_risk(stack: Stack) -> None:
    couple_id, first, _ = await stack.ready_couple("x_carrier", "no_findings")
    body = await run(stack, couple_id, first)
    assert body["outcome"] == "none_shared"
    assert "doesn't mean there's no risk" in body["notice"]


async def test_yes_or_no_returns_no_gene_names(stack: Stack) -> None:
    """V3.3.3."""
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    for headers in (first, second):
        response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=headers)
        assert "HBB" not in response.text
        body = response.json()
        assert body["reveal_level"] == "yes_no"
        assert body["shared_genes"] is None
        assert all(fact["gene"] is None for fact in body["facts"])


async def test_genes_appear_only_if_both_agreed(stack: Stack) -> None:
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid", reveals=("genes", "genes"))
    body = await run(stack, couple_id, first)
    assert body["reveal_level"] == "genes"
    assert body["shared_genes"] == ["HBB"]


@pytest.mark.parametrize("reveals", [("genes", "yes_no"), ("yes_no", "genes")])
async def test_the_more_private_choice_wins(stack: Stack, reveals: tuple[str, str]) -> None:
    """V3.3.9."""
    couple_id, first, second = await stack.ready_couple("fatima", "khalid", reveals=reveals)
    for headers in (first, second):
        response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=headers)
        assert response.json()["reveal_level"] == "yes_no"
        assert "HBB" not in response.text


async def test_a_partner_only_gene_appears_nowhere(
    stack: Stack, caplog: pytest.LogCaptureFixture
) -> None:
    """V3.3.4 (C7). Scans everything the partner can reach, for two kinds of private finding."""
    caplog.set_level("DEBUG")
    in_table, outside_table = "SMN1", "USH2A"
    holder = SyntheticPerson(
        "holder",
        "784-0000-0000101-1",
        Sex.FEMALE,
        (finding("HBB"), finding(in_table), finding(outside_table)),
    )
    await stack.ingest(build_bundle(holder, stack.pack, stack.panel))
    await stack.ingest(bundle_for("khalid"))
    first_headers = stack.headers(sub="holder-login", national_id=holder.national_id)
    await stack.http.post("/v1/me", json={}, headers=first_headers)
    await stack.http.post(
        "/v1/me/service-consent",
        json={"terms_version": "1", "accepted": True},
        headers=first_headers,
    )
    second = await stack.sign_in("khalid-login", "khalid")
    couple_id = await stack.link_couple(first_headers, second)
    await stack.agree_to_match(couple_id, first_headers, "genes")
    await stack.agree_to_match(couple_id, second, "genes")

    seen: list[str] = []
    for method, path in (
        ("POST", f"/v1/couples/{couple_id}/match"),
        ("GET", f"/v1/couples/{couple_id}"),
        ("GET", "/v1/couples"),
        ("GET", "/v1/consents"),
        ("GET", "/v1/me/results"),
        ("GET", "/v1/me/risk"),
        ("GET", "/v1/me/access-log"),
    ):
        response = await stack.http.request(method, path, headers=second)
        assert response.status_code == 200, path
        seen.append(response.text)
    match_body = await run(stack, couple_id, second)
    assert match_body["shared_genes"] == ["HBB"], "the test has to reach real data"

    # What the partner's chat would be given, once chat exists.
    pack = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
    assessment = couple_assessment(
        PartnerRecord(holder.findings, Sex.FEMALE, pack.gene_table.panel(stack.panel)),
        PartnerRecord(
            stack.people["khalid"].findings, Sex.MALE, pack.gene_table.panel(stack.panel)
        ),
        Relationship.UNRELATED,
        pack.gene_table,
    )
    context = build_llm_facts(partner_view(assessment, Viewer.B, Reveal.GENES))
    seen.append(repr(context))

    async with stack.factory() as session:
        audit_rows = (await session.scalars(select(AuditLog))).all()
    seen.append(" ".join(f"{row.resource} {row.action} {row.meta}" for row in audit_rows))
    seen.append(caplog.text)
    seen.extend(str(record.__dict__) for record in caplog.records)

    for text in seen:
        for marker in (in_table, outside_table):
            assert marker not in text


async def test_a_gene_list_in_the_request_is_refused(stack: Stack) -> None:
    """V3.3.5. Otherwise someone could test every gene against their partner's results."""
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid")
    response = await stack.http.post(
        f"/v1/couples/{couple_id}/match", json={"genes": ["HBB", "SMN1"]}, headers=first
    )
    assert response.status_code == 422


async def test_withdrawing_blocks_the_next_match(stack: Stack) -> None:
    """V3.3.6."""
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    await run(stack, couple_id, first)
    assert (
        await stack.http.delete(f"/v1/couples/{couple_id}/consent", headers=second)
    ).status_code == 204
    blocked = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=first)
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "match_not_ready"
    assert "HBB" not in blocked.text


async def test_withdrawing_twice_is_fine(stack: Stack) -> None:
    couple_id, _, second = await stack.ready_couple("fatima", "khalid")
    for _ in range(2):
        response = await stack.http.delete(f"/v1/couples/{couple_id}/consent", headers=second)
        assert response.status_code == 204


async def test_no_match_until_both_agree(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("khalid-login", "khalid")
    couple_id = await stack.link_couple(first, second)
    await stack.agree_to_match(couple_id, first)
    response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=first)
    assert response.status_code == 409


async def test_a_partner_is_not_shown_the_others_choices(stack: Stack) -> None:
    """Threat model: no record of a refusal reaches the partner, in any response or log."""
    await stack.ingest(bundle_for("fatima"))
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("khalid-login")
    couple_id = await stack.link_couple(first, second)
    await stack.agree_to_match(couple_id, second)
    await stack.http.delete(f"/v1/couples/{couple_id}/consent", headers=second)

    body = (await stack.http.get(f"/v1/couples/{couple_id}", headers=first)).json()
    assert body["my_consent_id"] is None
    assert set(body) == {
        "id", "partner_joined", "my_consent_id", "my_reveal_level", "what_a_result_reveals", "follow_up",
    }  # fmt: skip
    log = (await stack.http.get("/v1/me/access-log", headers=first)).json()["entries"]
    assert not [entry for entry in log if entry["action"].startswith("consent.couple")]


async def test_both_partners_can_see_the_follow_up(stack: Stack) -> None:
    """V3.3.7. Only one of them ran the match. The other still gets care, not just news."""
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    body = await run(stack, couple_id, first)
    assert body["follow_up_case_id"] is not None
    for headers in (first, second):
        couple = (await stack.http.get(f"/v1/couples/{couple_id}", headers=headers)).json()
        assert couple["follow_up"] is not None
        assert couple["follow_up"]["state"] == "COUNSELLING_REQUESTED"
    async with stack.factory() as session:
        cases = (await session.scalars(select(CareCase))).all()
    assert {case.priority for case in cases} == {"P2"}
    assert {str(case.couple_id) for case in cases} == {couple_id}
    assert len(cases) == 2


async def test_repeating_a_match_adds_no_cases(stack: Stack) -> None:
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    await run(stack, couple_id, first)
    await run(stack, couple_id, second)
    await run(stack, couple_id, first)
    async with stack.factory() as session:
        assert len((await session.scalars(select(CareCase))).all()) == 2


async def test_each_person_sees_their_own_case_only(stack: Stack) -> None:
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    first_id = (await run(stack, couple_id, first))["follow_up_case_id"]
    second_id = (await run(stack, couple_id, second))["follow_up_case_id"]
    assert first_id != second_id


async def test_the_audit_row_holds_no_genes(stack: Stack) -> None:
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid", reveals=("genes", "genes"))
    await run(stack, couple_id, first)
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog))).all()
        assert (await stack.audit.verify_chain(session)).intact
    match_row = next(row for row in rows if row.action == "match.run")
    assert match_row.meta == {"reveal": "genes", "mode": "shared"}


async def test_strangers_get_the_same_404_as_for_nothing_there(stack: Stack) -> None:
    couple_id, _, _ = await stack.ready_couple("fatima", "khalid")
    stranger = await stack.sign_in("stranger")
    real = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=stranger)
    absent = await stack.http.post(f"/v1/couples/{uuid.uuid4()}/match", headers=stranger)
    assert real.status_code == absent.status_code == 404
    assert real.json()["code"] == absent.json()["code"]
    assert real.json()["message"] == absent.json()["message"]


async def test_members_are_refused_during_an_outage(stack: Stack) -> None:
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid")
    stack.cut_off_authorisation()
    response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=first)
    assert response.status_code == 404
    await stack.app.state.authz.aclose()


async def test_an_invite_code_works_once(stack: Stack) -> None:
    first = await stack.sign_in("first")
    second = await stack.sign_in("second")
    third = await stack.sign_in("third")
    code = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["invite_code"]
    assert (
        await stack.http.post("/v1/couples/join", json={"invite_code": code}, headers=second)
    ).status_code == 200
    reused = await stack.http.post("/v1/couples/join", json={"invite_code": code}, headers=third)
    unknown = await stack.http.post(
        "/v1/couples/join", json={"invite_code": "x" * 22}, headers=third
    )
    assert reused.status_code == unknown.status_code == 404
    # The code's hash goes once used, so a stolen copy of the database can't be used to join.
    async with stack.factory() as session:
        from app.models.couple import Couple

        couple = await session.scalar(select(Couple))
        assert couple is not None
        assert couple.invite_code_hash is None
        assert couple.invite_expires_at is None
    assert reused.json()["code"] == unknown.json()["code"]


async def test_nobody_can_pair_with_themselves(stack: Stack) -> None:
    first = await stack.sign_in("first")
    code = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["invite_code"]
    response = await stack.http.post("/v1/couples/join", json={"invite_code": code}, headers=first)
    assert response.status_code == 404


async def test_consent_needs_the_disclosure_accepted(stack: Stack) -> None:
    """S8. A "yes" isn't fully blind, so the person has to have been told so."""
    first = await stack.sign_in("first")
    couple_id = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["id"]
    for accepted in ({}, {"understood_what_a_result_reveals": False}):
        response = await stack.http.post(
            f"/v1/couples/{couple_id}/consent",
            json={"reveal_level": "yes_no", "terms_version": "1", **accepted},
            headers=first,
        )
        assert response.status_code == 422


async def test_the_disclosure_says_plainly_what_a_yes_reveals(stack: Stack) -> None:
    first = await stack.sign_in("first")
    couple_id = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["id"]
    body = (await stack.http.get(f"/v1/couples/{couple_id}", headers=first)).json()
    assert "which gene" in body["what_a_result_reveals"]
    assert "server" in body["what_a_result_reveals"]


async def test_changing_a_choice_keeps_the_earlier_one_on_record(stack: Stack) -> None:
    first = await stack.sign_in("first")
    couple_id = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["id"]
    await stack.agree_to_match(couple_id, first, "genes")
    await stack.agree_to_match(couple_id, first, "yes_no")
    given = (await stack.http.get("/v1/consents", headers=first)).json()["given"]
    choices = [item for item in given if item["kind"] == "couple_match"]
    assert sorted((item["reveal_level"], item["active"]) for item in choices) == [
        ("genes", False),
        ("yes_no", True),
    ]


async def test_choosing_not_to_know_stops_the_match(stack: Stack) -> None:
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=second
    )
    assert (
        await stack.http.post(f"/v1/couples/{couple_id}/match", headers=first)
    ).status_code == 409


async def test_partners_in_different_countries_get_no_result(stack: Stack) -> None:
    """Each pack has its own gene table, and nothing says which should apply."""
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("rohan", pack=INDIA), pack=INDIA)
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("rohan-login", "rohan", pack=INDIA)
    couple_id = await stack.link_couple(first, second)
    await stack.agree_to_match(couple_id, first)
    await stack.agree_to_match(couple_id, second)
    assert (await run(stack, couple_id, first))["outcome"] == "cannot_determine"


def test_the_more_private_level_is_chosen() -> None:
    assert effective_reveal("genes", "genes").value == "genes"
    assert effective_reveal("yes_no", "genes").value == "yes_no"
    assert effective_reveal("genes", "yes_no").value == "yes_no"
    assert effective_reveal("yes_no", "yes_no").value == "yes_no"


@pytest.mark.parametrize(
    ("reports", "expected"),
    [
        (["unrelated", "first_cousins"], Relationship.FIRST_COUSINS),
        (["first_cousins", "unrelated"], Relationship.FIRST_COUSINS),
        (["second_cousins", "double_first_cousins"], Relationship.DOUBLE_FIRST_COUSINS),
        (["unknown", "second_cousins"], Relationship.SECOND_COUSINS),
        (["unrelated"], Relationship.UNRELATED),
        ([], Relationship.UNKNOWN),
    ],
)
def test_when_accounts_differ_the_closer_relationship_counts(
    reports: list[str], expected: Relationship
) -> None:
    assert effective_relationship(reports) is expected


PACK = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")


def assessed(a: list[Finding], b: list[Finding], b_tested: bool = True) -> Any:
    panel = PACK.gene_table.panel("demo-panel-v1")
    return couple_assessment(
        PartnerRecord(tuple(a), Sex.FEMALE, panel),
        PartnerRecord(tuple(b), Sex.MALE, panel if b_tested else None),
        Relationship.UNRELATED,
        PACK.gene_table,
    )


@pytest.mark.parametrize(
    ("a", "b", "b_tested", "expected"),
    [
        (["HBB"], ["HBB"], True, MatchOutcome.SHARED),
        (["HBB"], [], True, MatchOutcome.NONE_SHARED),
        ([], [], True, MatchOutcome.NONE_SHARED),
        # The partner was never tested for this gene, so this can't count as a negative.
        (["HBB"], [], False, MatchOutcome.CANNOT_DETERMINE),
        # The rules can't assess a gene outside the pack.
        (["USH2A"], [], True, MatchOutcome.CANNOT_DETERMINE),
        # These two genes interact, so it goes to a person.
        (["HBA1"], ["HBA2"], True, MatchOutcome.CANNOT_DETERMINE),
    ],
)
def test_outcomes(a: list[str], b: list[str], b_tested: bool, expected: MatchOutcome) -> None:
    result = assessed([finding(g) for g in a], [finding(g) for g in b], b_tested)
    assert _outcome(result) is expected


def test_a_shared_uncertain_finding_cannot_read_as_none() -> None:
    vus = Finding("HBB", Classification.UNCERTAIN, Zygosity.HETEROZYGOUS, "c.1A>G")
    assert _outcome(assessed([vus], [finding("HBB")])) is MatchOutcome.CANNOT_DETERMINE


async def test_an_openfga_tuple_alone_does_not_make_someone_a_member(stack: Stack) -> None:
    """Either layer alone is enough to say no."""
    couple_id, _, _ = await stack.ready_couple("fatima", "khalid")
    stranger = await stack.sign_in("stranger")
    authz: Authz = stack.app.state.authz
    await authz.write(
        RelationTuple(f"user:{await stack.person_id(stranger)}", "member", f"couple:{couple_id}")
    )
    response = await stack.http.post(f"/v1/couples/{couple_id}/match", headers=stranger)
    assert response.status_code == 404


async def test_an_expired_invite_code_is_refused(stack: Stack) -> None:
    first = await stack.sign_in("first")
    second = await stack.sign_in("second")
    code = (await stack.http.post("/v1/couples", json={}, headers=first)).json()["invite_code"]
    authz: Authz = stack.app.state.authz
    now = authz.clock()
    authz.clock = lambda: now + timedelta(days=8)
    response = await stack.http.post("/v1/couples/join", json={"invite_code": code}, headers=second)
    assert response.status_code == 404


async def test_either_partner_choosing_not_to_know_stops_the_match(stack: Stack) -> None:
    couple_id, first, second = await stack.ready_couple("fatima", "khalid")
    await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=first
    )
    assert (
        await stack.http.post(f"/v1/couples/{couple_id}/match", headers=second)
    ).status_code == 409


@pytest.mark.parametrize("untrusted", ["fatima", "khalid"])
async def test_one_untrusted_report_is_enough_to_give_no_result(
    stack: Stack, untrusted: str
) -> None:
    """Each partner's report is checked on its own, so either one being untrusted counts."""
    couple_id, first, _ = await stack.ready_couple("fatima", "khalid")
    national_id = stack.people[untrusted].national_id
    from sqlalchemy import update

    from app.models.genetic import GeneticReport
    from app.models.person import Person

    async with stack.factory() as session:
        person = await session.scalar(
            select(Person).where(Person.keycloak_sub == f"{untrusted}-login")
        )
        assert person is not None
        await session.execute(
            update(GeneticReport)
            .where(GeneticReport.person_id == person.id)
            .values(attestation="unverified")
        )
        await session.commit()
    assert national_id
    assert (await run(stack, couple_id, first))["outcome"] == "cannot_determine"
