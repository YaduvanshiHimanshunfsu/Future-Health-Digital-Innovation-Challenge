import asyncio
import copy
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.community.postgres import PostgresContainer

from app.models.audit import AuditLog
from app.models.case import CareCase, PathwayStep
from app.models.genetic import CarrierFinding, GeneticReport
from app.models.person import Person
from app.repositories.genetic import load_record
from synthetic.generate import SyntheticPerson, build_bundle
from tests.api.helpers import AD, INDIA, Stack, bundle_for, with_binary_columns_decoded

pytestmark = pytest.mark.db


async def test_report_is_stored_and_benign_variant_dropped(stack: Stack) -> None:
    """V2.3.1. The persona has one benign variant, which must leave no trace."""
    response = await stack.ingest(bundle_for("no_findings"))
    assert response.status_code == 201
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(CarrierFinding)) == 0
        assert await session.scalar(select(func.count()).select_from(GeneticReport)) == 1


async def test_replay_returns_the_same_report_and_adds_nothing(stack: Stack) -> None:
    """V2.3.2."""
    first = await stack.ingest(bundle_for("fatima"))
    second = await stack.ingest(bundle_for("fatima"))
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == {"report_id": first.json()["report_id"], "replayed": True}
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(GeneticReport)) == 1
        assert await session.scalar(select(func.count()).select_from(CarrierFinding)) == 1
        assert await session.scalar(select(func.count()).select_from(CareCase)) == 1


async def test_same_version_with_different_contents_is_refused(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    changed = bundle_for("fatima")
    changed["entry"][0]["resource"]["gender"] = "male"
    response = await stack.ingest(changed)
    assert response.status_code == 409
    assert response.json()["code"] == "report_version_conflict"


async def test_second_report_for_one_person_succeeds(stack: Stack) -> None:
    """V2.3.3. In the original spec this failed on a duplicate authorisation tuple."""
    await stack.ingest(bundle_for("fatima"))
    response = await stack.ingest(bundle_for("fatima", report_id="DEMO-second"))
    assert response.status_code == 201
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(Person)) == 1
        assert await session.scalar(select(func.count()).select_from(GeneticReport)) == 2


async def test_amended_report_supersedes_the_earlier_version(stack: Stack) -> None:
    """A variant can be reclassified later. Old findings stay on record but are no longer read."""
    await stack.ingest(bundle_for("uncertain"))
    amended = SyntheticPerson(
        "uncertain",
        "784-0000-0000006-1",
        stack.people["uncertain"].sex,
        stack.people["fatima"].findings,
    )
    response = await stack.ingest(
        build_bundle(
            amended,
            stack.pack,
            stack.panel,
            version=2,
            status="amended",
            report_id="DEMO-uncertain",
        )
    )
    assert response.status_code == 201
    async with stack.factory() as session:
        person = await session.scalar(select(Person))
        assert person is not None
        record = await load_record(session, stack.cipher, person.id)
        assert [finding.gene for finding in record.findings] == ["HBB"]
        reports = (
            await session.scalars(select(GeneticReport).order_by(GeneticReport.report_version))
        ).all()
        assert reports[0].superseded_at is not None
        assert reports[1].superseded_at is None
        assert await session.scalar(select(func.count()).select_from(CarrierFinding)) == 2


async def test_older_version_arriving_late_is_refused(stack: Stack) -> None:
    await stack.ingest(build_bundle(stack.people["fatima"], stack.pack, stack.panel, version=3))
    response = await stack.ingest(bundle_for("fatima"))
    assert response.status_code == 409
    assert response.json()["code"] == "report_version_outdated"


def _break(mutate: Any) -> dict[str, Any]:
    bundle = copy.deepcopy(bundle_for("fatima"))
    mutate(bundle)
    return bundle


def _observation(bundle: dict[str, Any]) -> dict[str, Any]:
    return next(
        e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"
    )


MALFORMED = {
    "a_list": ["not", "a", "bundle"],
    "a_string": "bundle",
    "a_number": 7,
    "null": None,
    "wrong_resource": {"resourceType": "Patient"},
    "no_entries": {"resourceType": "Bundle", "type": "collection"},
    "entries_not_a_list": {"resourceType": "Bundle", "type": "collection", "entry": "x"},
    "empty_entries": {"resourceType": "Bundle", "type": "collection", "entry": []},
    "bad_type": _break(lambda b: b.update(type="nonsense")),
    "entry_not_a_dict": _break(lambda b: b["entry"].append("x")),
    "too_many_entries": _break(lambda b: b["entry"].extend([b["entry"][0]] * 2001)),
    "no_patient": _break(lambda b: b["entry"].pop(0)),
    "no_report": _break(lambda b: b["entry"].pop(1)),
    "two_patients": _break(lambda b: b["entry"].append(b["entry"][0])),
    "wrong_id_system": _break(
        lambda b: b["entry"][0]["resource"]["identifier"][0].update(system="urn:other")
    ),
    "preliminary": _break(lambda b: b["entry"][1]["resource"].update(status="preliminary")),
    "no_report_id": _break(lambda b: b["entry"][1]["resource"].pop("identifier")),
    "bad_version": _break(lambda b: b["entry"][1]["resource"]["meta"].update(versionId="abc")),
    "no_panel": _break(lambda b: b["entry"][1]["resource"]["code"]["coding"][0].pop("code")),
    "invalid_fhir_field": _break(lambda b: b["entry"][0]["resource"].update(gender=123)),
    "unknown_significance": _break(
        lambda b: _observation(b)["component"][2]["valueCodeableConcept"]["coding"][0].update(
            code="LA-UNKNOWN"
        )
    ),
    "missing_significance": _break(lambda b: _observation(b)["component"].pop(2)),
    "bad_gene_symbol": _break(
        lambda b: _observation(b)["component"][0]["valueCodeableConcept"]["coding"][0].update(
            display="<script>"
        )
    ),
    "bad_hgvs": _break(
        lambda b: _observation(b)["component"][1]["valueCodeableConcept"]["coding"][0].update(
            code="'; DROP TABLE"
        )
    ),
    "missing_zygosity": _break(lambda b: _observation(b)["component"].pop(3)),
}


@pytest.mark.parametrize("name", MALFORMED)
async def test_malformed_input_gets_422_and_stores_nothing(stack: Stack, name: str) -> None:
    """V2.3.4. An unrecognised significance is refused, not dropped: it could be pathogenic."""
    response = await stack.ingest(MALFORMED[name])
    assert response.status_code == 422, response.text
    assert "784" not in response.text
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(Person)) == 0


async def test_unknown_panel_is_refused(stack: Stack) -> None:
    bundle = build_bundle(stack.people["fatima"], stack.pack, "no-such-panel")
    response = await stack.ingest(bundle)
    assert response.status_code == 422
    assert response.json()["code"] == "unknown_panel"


async def test_unknown_country_pack_is_refused(stack: Stack) -> None:
    response = await stack.ingest(bundle_for("fatima"), pack="zz-nowhere")
    assert response.status_code == 422
    assert response.json()["code"] == "unknown_country_pack"


async def test_gene_outside_the_pack_is_kept_and_referred(stack: Stack) -> None:
    response = await stack.ingest(bundle_for("gene_not_in_pack"))
    assert response.status_code == 201
    case = await stack.only_case()
    assert case.priority == "P3"


async def test_only_a_lab_can_ingest(stack: Stack) -> None:
    assert (await stack.ingest(bundle_for("fatima"), roles=["individual"])).status_code == 403
    assert (await stack.http.post("/v1/reports:ingest", json={})).status_code == 401


async def test_demo_attestation_is_recorded_and_readable(stack: Stack) -> None:
    """V2.3.5. In the original spec nothing could ever be attested, so matches found nothing."""
    await stack.ingest(bundle_for("fatima"))
    async with stack.factory() as session:
        report = await session.scalar(select(GeneticReport))
        assert report is not None
        assert report.attestation == "demo"
        record = await load_record(session, stack.cipher, report.person_id, trusted_only=True)
        assert record.has_report
        assert [finding.gene for finding in record.findings] == ["HBB"]


async def test_unattested_report_is_not_read_as_trusted_and_says_so(
    stack: Stack, make_stack: Any
) -> None:
    """An untrusted report must read as "no trusted report", never as "nothing found"."""
    other = await make_stack(lab_attestation="unverified")
    await other.ingest(bundle_for("fatima"))
    async with other.factory() as session:
        report = await session.scalar(select(GeneticReport))
        assert report is not None
        trusted = await load_record(session, other.cipher, report.person_id, trusted_only=True)
        assert not trusted.has_report
        everything = await load_record(session, other.cipher, report.person_id)
        assert everything.has_report


@pytest.mark.parametrize(
    ("persona", "priority", "state"),
    [
        ("x_man", "P1", "COUNSELLING_REQUESTED"),
        ("two_variants", "P1", "COUNSELLING_REQUESTED"),
        ("x_carrier", "P2", "COUNSELLING_REQUESTED"),
        ("uncertain", "P3", "RESULT_RELEASED"),
        ("fatima", "P4", "RESULT_RELEASED"),
    ],
)
async def test_triage_runs_when_a_result_arrives(
    stack: Stack, persona: str, priority: str, state: str
) -> None:
    """V2.3.6. In the original spec, an affected adult waited unless they opened the chat."""
    assert (await stack.ingest(bundle_for(persona))).status_code == 201
    case = await stack.only_case()
    assert case.priority == priority
    assert case.state == state


async def test_every_case_change_leaves_a_step(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_man"))
    async with stack.factory() as session:
        steps = (await session.scalars(select(PathwayStep))).all()
    assert {step.to_state for step in steps} == {"RESULT_RELEASED", "COUNSELLING_REQUESTED"}


async def test_a_later_result_only_raises_priority(stack: Stack) -> None:
    await stack.ingest(bundle_for("uncertain"))
    assert (await stack.only_case()).priority == "P3"

    worse = SyntheticPerson(
        "u2",
        "784-0000-0000006-1",
        stack.people["uncertain"].sex,
        stack.people["two_variants"].findings,
    )
    await stack.ingest(build_bundle(worse, stack.pack, stack.panel))
    case = await stack.only_case()
    assert case.priority == "P1"
    assert case.state == "COUNSELLING_REQUESTED"
    assert sorted(
        await stack.cipher.decrypt_json(case.reasons_enc, aad=f"care_case:{case.id}:reasons")
    ) == [
        "possibly_affected",
        "uncertain_finding",
    ]

    better = SyntheticPerson("u3", "784-0000-0000006-1", stack.people["uncertain"].sex, ())
    await stack.ingest(build_bundle(better, stack.pack, stack.panel))
    assert (await stack.only_case()).priority == "P1"


async def test_time_target_comes_from_the_pack(stack: Stack) -> None:
    """V2.6.8. The same priority gets each country's own deadline."""
    await stack.ingest(bundle_for("x_carrier"))
    await stack.ingest(bundle_for("x_carrier_in", pack=INDIA), pack=INDIA)
    async with stack.factory() as session:
        cases = {
            person.pack_code: case
            for case, person in (
                await session.execute(
                    select(CareCase, Person).join(Person, CareCase.subject_id == Person.id)
                )
            ).all()
        }
    gap = cases[INDIA].step_due - cases[AD].step_due
    assert 95 < gap.total_seconds() / 3600 < 97


async def test_ingest_is_audited_without_health_details(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog).order_by(AuditLog.seq))).all()
        report = await stack.audit.verify_chain(session)
    assert report.intact
    assert "report.ingest" in [row.action for row in rows]
    text = " ".join(f"{row.resource} {row.meta}" for row in rows)
    assert "HBB" not in text
    assert "784" not in text


async def test_raw_database_holds_no_genetic_or_identity_details(
    stack: Stack, postgres: PostgresContainer, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """V2.1.4. Reads an actual dump of the database, the way someone with a stolen copy would."""
    for persona in ("fatima", "two_variants", "x_carrier", "uncertain"):
        assert (await stack.ingest(bundle_for(persona))).status_code == 201

    result = postgres.get_wrapped_container().exec_run(
        ["pg_dump", "-U", "postgres", "--data-only", "--inserts", "samvid"]
    )
    assert result.exit_code == 0
    dump = result.output.decode("utf-8", "replace")
    assert "INSERT INTO public.carrier_finding" in dump
    # pg_dump writes binary columns as hex, so a plain search would pass even with no encryption.
    dump = with_binary_columns_decoded(dump)
    for secret in (
        "HBB",
        "DMD",
        "CYP21A2",
        "c.20A",
        "784-0000",
        "possibly_affected",
        "x_linked",
        '"sex"',
    ):
        assert secret not in dump, secret


async def test_reusing_a_report_id_for_another_person_is_refused(stack: Stack) -> None:
    """Going on would cancel the first person's result because of a second person's report."""
    await stack.ingest(bundle_for("fatima", report_id="DEMO-shared"))
    wrong = build_bundle(
        stack.people["khalid"], stack.pack, stack.panel, version=2, report_id="DEMO-shared"
    )
    response = await stack.ingest(wrong)
    assert response.status_code == 409
    assert response.json()["code"] == "report_subject_conflict"
    async with stack.factory() as session:
        report = await session.scalar(select(GeneticReport))
        assert report is not None
        assert report.superseded_at is None
        assert await session.scalar(select(func.count()).select_from(Person)) == 1


async def test_two_first_reports_arriving_together_make_one_person(stack: Stack) -> None:
    responses = await asyncio.gather(
        stack.ingest(bundle_for("fatima", report_id="DEMO-a")),
        stack.ingest(bundle_for("fatima", report_id="DEMO-b")),
    )
    assert [response.status_code for response in responses] == [201, 201]
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(Person)) == 1
        assert await session.scalar(select(func.count()).select_from(GeneticReport)) == 2
        assert await session.scalar(select(func.count()).select_from(CareCase)) == 1
        assert (await stack.audit.verify_chain(session)).intact


def test_the_dump_search_can_see_inside_binary_columns() -> None:
    """Without this, the search above could go blind again and still pass."""
    readable = b'{"gene":"HBB"}'.hex()
    dump = f"INSERT INTO public.carrier_finding VALUES ('\\x{readable}');"
    assert "HBB" not in dump
    assert "HBB" in with_binary_columns_decoded(dump)


async def test_every_finding_is_stored_as_ciphertext(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    async with stack.factory() as session:
        finding = await session.scalar(select(CarrierFinding))
        person = await session.scalar(select(Person))
    assert finding is not None
    assert person is not None
    assert person.clinical_enc is not None
    for blob in (finding.payload_enc, person.clinical_enc):
        assert blob[0] == 1, "starts with the record format version"
        assert b"HBB" not in blob
        assert b'"sex"' not in blob
        assert b"{" not in blob[:2]
