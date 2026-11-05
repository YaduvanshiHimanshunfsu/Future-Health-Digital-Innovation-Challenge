import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.country_packs.loader import CountryPack
from app.ingestion.fhir_parser import BundleError, ParsedReport, parse_report
from app.models.enums import Attestation
from app.models.genetic import CarrierFinding, GeneticReport
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.risk_engine.engine import person_facts
from app.triage.service import triage_result


def national_id_hash(key: bytes, pack: CountryPack, raw: str) -> str:
    # The pack code is part of the input so equal numbers in two countries stay separate people.
    message = f"{pack.code}:{pack.normalise_national_id(raw)}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def clinical_aad(person_id: uuid.UUID) -> str:
    return f"person:{person_id}:clinical"


def finding_aad(finding_id: uuid.UUID) -> str:
    return f"carrier_finding:{finding_id}"


@dataclass(frozen=True, slots=True)
class IngestResult:
    report: GeneticReport
    replayed: bool


@dataclass(frozen=True, slots=True)
class IngestContext:
    national_id_key: bytes
    cipher: FieldCipher
    audit: AuditTrail
    attestation: Attestation


async def _find_or_create_person(
    db: AsyncSession, ctx: IngestContext, pack: CountryPack, parsed: ParsedReport
) -> Person:
    id_hash = national_id_hash(ctx.national_id_key, pack, parsed.national_id)
    by_id = select(Person).where(Person.national_id_hash == id_hash)
    person = await db.scalar(by_id)
    if person is None:
        # Results can arrive before someone's first sign-in. They link up on that first sign-in.
        person = Person(
            id=uuid.uuid4(),
            national_id_hash=id_hash,
            pack_code=pack.code,
            preferred_lang=pack.manifest.default_language,
        )
        try:
            async with db.begin_nested():
                db.add(person)
        except IntegrityError:
            # Two reports for someone new can arrive together. The first creates the person, and
            # this one waits on the unique index and then joins them.
            person = (await db.scalars(by_id)).one()
    person.clinical_enc = await ctx.cipher.encrypt_json(
        {"sex": parsed.sex.value}, aad=clinical_aad(person.id)
    )
    await db.flush()
    return person


async def ingest_bundle(
    db: AsyncSession,
    ctx: IngestContext,
    *,
    bundle: Any,
    pack: CountryPack,
    source_lab: str,
    actor: str,
) -> IngestResult:
    try:
        parsed = parse_report(bundle, national_id_system=pack.identity.national_id_fhir_system)
    except BundleError:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_bundle") from None
    if pack.gene_table.panel(parsed.panel_version) is None:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "unknown_panel")

    digest = hashlib.sha256(
        json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    existing = (
        await db.scalars(
            select(GeneticReport).where(
                GeneticReport.source_lab == source_lab,
                GeneticReport.source_report_id == parsed.report_id,
            )
        )
    ).all()
    for report in existing:
        if report.report_version == parsed.report_version:
            if report.bundle_sha256 == digest:
                return IngestResult(report, replayed=True)
            # The same version with different contents means someone made a mistake. Refusing
            # keeps the record of what was actually delivered.
            raise ApiError(HTTPStatus.CONFLICT, "report_version_conflict")
    if existing and parsed.report_version < max(r.report_version for r in existing):
        raise ApiError(HTTPStatus.CONFLICT, "report_version_outdated")

    person = await _find_or_create_person(db, ctx, pack, parsed)
    if any(report.person_id != person.id for report in existing):
        # An amendment names the person the report was about. If that changes, the lab has made a
        # mistake, and going on would cancel the first person's result on a second person's data.
        raise ApiError(HTTPStatus.CONFLICT, "report_subject_conflict")
    await db.execute(
        update(GeneticReport)
        .where(
            GeneticReport.source_lab == source_lab,
            GeneticReport.source_report_id == parsed.report_id,
            GeneticReport.superseded_at.is_(None),
        )
        .values(superseded_at=datetime.now(UTC))
    )
    report = GeneticReport(
        person_id=person.id,
        source_lab=source_lab,
        source_report_id=parsed.report_id,
        report_version=parsed.report_version,
        panel_version=parsed.panel_version,
        bundle_sha256=digest,
        attestation=ctx.attestation.value,
    )
    db.add(report)
    try:
        await db.flush()
    except IntegrityError:
        # Lost a race with an identical delivery, so that one stands.
        raise ApiError(HTTPStatus.CONFLICT, "report_version_conflict") from None

    for finding in parsed.findings:
        finding_id = uuid.uuid4()
        db.add(
            CarrierFinding(
                id=finding_id,
                report_id=report.id,
                payload_enc=await ctx.cipher.encrypt_json(
                    {
                        "gene": finding.gene,
                        "classification": finding.classification.value,
                        "zygosity": finding.zygosity.value,
                        "variant": finding.variant,
                    },
                    aad=finding_aad(finding_id),
                ),
            )
        )
    await db.flush()

    facts = person_facts(parsed.findings, parsed.sex, pack.gene_table)
    await triage_result(
        db, ctx.cipher, ctx.audit, person=person, pack=pack, facts=facts, actor=actor
    )

    # Written last, because the chain lock is held from here until commit.
    await ctx.audit.append(
        db,
        actor=actor,
        action="report.ingest",
        resource=f"person:{person.id}",
        meta={
            "count": len(parsed.findings),
            "rule_version": facts[0].rule_version if facts else None,
        },
    )
    return IngestResult(report, replayed=False)
