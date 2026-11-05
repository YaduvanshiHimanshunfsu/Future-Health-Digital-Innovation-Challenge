import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.service import clinical_aad, finding_aad
from app.models.enums import Attestation
from app.models.genetic import CarrierFinding, GeneticReport
from app.models.person import Person
from app.privacy.crypto import FieldCipher
from app.risk_engine.types import Classification, Finding, Sex, Zygosity

TRUSTED = (Attestation.VERIFIED.value, Attestation.DEMO.value)


@dataclass(frozen=True, slots=True)
class GeneticRecord:
    findings: tuple[Finding, ...]
    panel_versions: frozenset[str]
    has_report: bool
    attestations: frozenset[str]


async def load_record(
    db: AsyncSession, cipher: FieldCipher, person_id: uuid.UUID, *, trusted_only: bool = False
) -> GeneticRecord:
    """A person's current findings. The caller gets person_id from the token, never the client.

    `has_report` lets callers tell "nothing found" apart from "never tested", which must never be
    presented as the same thing.
    """
    conditions = [GeneticReport.person_id == person_id, GeneticReport.superseded_at.is_(None)]
    if trusted_only:
        conditions.append(GeneticReport.attestation.in_(TRUSTED))
    reports = (await db.scalars(select(GeneticReport).where(*conditions))).all()

    findings: list[Finding] = []
    for report in reports:
        rows = (
            await db.scalars(select(CarrierFinding).where(CarrierFinding.report_id == report.id))
        ).all()
        for row in rows:
            payload = await cipher.decrypt_json(row.payload_enc, aad=finding_aad(row.id))
            findings.append(
                Finding(
                    gene=payload["gene"],
                    classification=Classification(payload["classification"]),
                    zygosity=Zygosity(payload["zygosity"]),
                    variant=payload["variant"],
                )
            )
    return GeneticRecord(
        findings=tuple(findings),
        panel_versions=frozenset(report.panel_version for report in reports),
        has_report=bool(reports),
        attestations=frozenset(report.attestation for report in reports),
    )


async def person_sex(cipher: FieldCipher, person: Person) -> Sex:
    if person.clinical_enc is None:
        return Sex.UNKNOWN
    payload = await cipher.decrypt_json(person.clinical_enc, aad=clinical_aad(person.id))
    return Sex(payload.get("sex", Sex.UNKNOWN.value))
