import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.country_packs.loader import CountryPack, PackRegistry
from app.models.case import CareCase
from app.models.consent import Consent
from app.models.couple import Couple
from app.models.enums import ConsentKind, RevealLevel
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.repositories.genetic import GeneticRecord, load_record, person_sex
from app.risk_engine import rules
from app.risk_engine.engine import couple_assessment, partner_view
from app.risk_engine.types import (
    CoupleAssessment,
    PartnerRecord,
    Relationship,
    Reveal,
    RiskFact,
    Scenario,
    Sex,
    Viewer,
)
from app.triage.scoring import score
from app.triage.service import open_or_escalate

INVITE_LIFETIME = timedelta(days=7)
_NOT_A_NEGATIVE = frozenset({Scenario.REFER, Scenario.COUPLE_ONE_CARRIER_UNTESTED})


class MatchOutcome(StrEnum):
    """ "None shared" is a result. "Can't determine" means there isn't one, and must never read as one."""

    SHARED = "shared"
    NONE_SHARED = "none_shared"
    CANNOT_DETERMINE = "cannot_determine"


class MatchNotReady(Exception):
    """Deliberately says nothing about which partner, or whether they declined or just haven't yet."""


@dataclass(frozen=True, slots=True)
class MatchResult:
    outcome: MatchOutcome
    reveal: RevealLevel
    facts: tuple[RiskFact, ...] = ()
    shared_genes: tuple[str, ...] | None = None
    case_id: uuid.UUID | None = None


def effective_reveal(first: str, second: str) -> RevealLevel:
    """The more private choice of the two always wins."""
    if RevealLevel.YES_NO.value in (first, second):
        return RevealLevel.YES_NO
    return RevealLevel.GENES


def invite_hash(key: bytes, code: str) -> str:
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()


def details_aad(couple_id: uuid.UUID) -> str:
    return f"couple:{couple_id}:details"


def effective_relationship(reports: list[str]) -> Relationship:
    """If the two accounts differ, the closer relationship is used, which gives the higher figure."""
    told = [Relationship(item) for item in reports] or [Relationship.UNKNOWN]
    return max(told, key=lambda relationship: rules.KINSHIP[relationship])


async def create_couple(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    *,
    actor: str,
    person: Person,
    relationship: Relationship,
    key: bytes,
    now: datetime,
) -> tuple[Couple, str]:
    code = secrets.token_urlsafe(16)
    couple_id = uuid.uuid4()
    couple = Couple(
        id=couple_id,
        person_a=person.id,
        invite_code_hash=invite_hash(key, code),
        invite_expires_at=now + INVITE_LIFETIME,
        details_enc=await cipher.encrypt_json(
            {"a": relationship.value}, aad=details_aad(couple_id)
        ),
    )
    db.add(couple)
    await db.flush()
    await audit.append(db, actor=actor, action="couple.create", resource=f"couple:{couple.id}")
    return couple, code


async def join_couple(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    *,
    actor: str,
    person: Person,
    code: str,
    relationship: Relationship,
    key: bytes,
    now: datetime,
) -> Couple | None:
    couple = await db.scalar(
        select(Couple).where(Couple.invite_code_hash == invite_hash(key, code)).with_for_update()
    )
    if (
        couple is None
        or couple.person_a == person.id
        or couple.person_b is not None
        or couple.invite_expires_at is None
        or couple.invite_expires_at <= now
    ):
        return None
    details = await _details(cipher, couple)
    couple.person_b = person.id
    couple.invite_code_hash = None
    couple.invite_expires_at = None
    couple.details_enc = await cipher.encrypt_json(
        {**details, "b": relationship.value}, aad=details_aad(couple.id)
    )
    await db.flush()
    await audit.append(db, actor=actor, action="couple.join", resource=f"couple:{couple.id}")
    return couple


async def _details(cipher: FieldCipher, couple: Couple) -> dict[str, str]:
    if couple.details_enc is None:
        return {}
    loaded: dict[str, str] = await cipher.decrypt_json(
        couple.details_enc, aad=details_aad(couple.id)
    )
    return loaded


async def live_match_consent(
    db: AsyncSession, person_id: uuid.UUID, couple_id: uuid.UUID
) -> Consent | None:
    consent: Consent | None = await db.scalar(
        select(Consent).where(
            Consent.grantor_id == person_id,
            Consent.couple_id == couple_id,
            Consent.kind == ConsentKind.COUPLE_MATCH.value,
            Consent.revoked_at.is_(None),
        )
    )
    return consent


def _tested_genes(record: GeneticRecord, pack: CountryPack) -> frozenset[str] | None:
    panels = [pack.gene_table.panel(version) for version in record.panel_versions]
    known = [panel for panel in panels if panel is not None]
    return frozenset().union(*known) if known else None


def _outcome(assessment: CoupleAssessment) -> MatchOutcome:
    if assessment.shared_genes:
        return MatchOutcome.SHARED
    if assessment.review_needed:
        return MatchOutcome.CANNOT_DETERMINE
    # A finding the partner was never tested for, or that the rules can't assess, isn't a negative.
    if any(item.fact.scenario in _NOT_A_NEGATIVE for item in assessment.facts):
        return MatchOutcome.CANNOT_DETERMINE
    return MatchOutcome.NONE_SHARED


async def match_couple(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    packs: PackRegistry,
    *,
    actor: str,
    couple: Couple,
    viewer: Person,
) -> MatchResult:
    """Input comes only from stored, trusted reports, never from the request (issue C7, S8).

    This runs on the server with both partners' findings in memory, and it isn't a blind protocol.
    What it does guarantee is that only the view built for this viewer leaves this function.
    """
    if couple.person_b is None:
        raise MatchNotReady
    first = await db.get(Person, couple.person_a)
    second = await db.get(Person, couple.person_b)
    if first is None or second is None:
        raise MatchNotReady
    first_consent = await live_match_consent(db, first.id, couple.id)
    second_consent = await live_match_consent(db, second.id, couple.id)
    if (
        first_consent is None
        or second_consent is None
        or first.results_withheld_at is not None
        or second.results_withheld_at is not None
    ):
        raise MatchNotReady

    reveal = effective_reveal(
        first_consent.reveal_level or RevealLevel.YES_NO.value,
        second_consent.reveal_level or RevealLevel.YES_NO.value,
    )
    result = await _assess(db, cipher, audit, packs, actor, couple, first, second, viewer, reveal)
    await audit.append(
        db,
        actor=actor,
        action="match.run",
        resource=f"couple:{couple.id}",
        meta={"reveal": reveal.value, "mode": result.outcome.value},
    )
    return result


async def _assess(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    packs: PackRegistry,
    actor: str,
    couple: Couple,
    first: Person,
    second: Person,
    viewer: Person,
    reveal: RevealLevel,
) -> MatchResult:
    undetermined = MatchResult(MatchOutcome.CANNOT_DETERMINE, reveal)
    # Different countries mean different gene tables, and no rule says which one should apply.
    if first.pack_code != second.pack_code:
        return undetermined
    pack = packs.require(first.pack_code)

    first_record = await load_record(db, cipher, first.id, trusted_only=True)
    second_record = await load_record(db, cipher, second.id, trusted_only=True)
    # No trusted report isn't the same as nothing found (issues C1 and C2).
    if not (first_record.has_report and second_record.has_report):
        return undetermined

    assessment = couple_assessment(
        await _partner(cipher, first, first_record, pack),
        await _partner(cipher, second, second_record, pack),
        effective_relationship(list((await _details(cipher, couple)).values())),
        pack.gene_table,
    )

    viewer_side = Viewer.A if viewer.id == first.id else Viewer.B
    case_id: uuid.UUID | None = None
    for person, side in ((first, Viewer.A), (second, Viewer.B)):
        # Internal only, to set priority. Each person's case holds generic reasons with no genes.
        triage = score(partner_view(assessment, side, Reveal.GENES))
        if triage is None:
            continue
        case = await open_or_escalate(
            db,
            cipher,
            audit,
            person=person,
            pack=pack,
            result=triage,
            actor=actor,
            couple_id=couple.id,
        )
        if side is viewer_side:
            case_id = case.id

    genes_allowed = reveal is RevealLevel.GENES
    return MatchResult(
        outcome=_outcome(assessment),
        reveal=reveal,
        facts=tuple(partner_view(assessment, viewer_side, Reveal(reveal.value))),
        shared_genes=tuple(sorted(assessment.shared_genes)) if genes_allowed else None,
        case_id=case_id,
    )


async def _partner(
    cipher: FieldCipher, person: Person, record: GeneticRecord, pack: CountryPack
) -> PartnerRecord:
    sex: Sex = await person_sex(cipher, person)
    return PartnerRecord(record.findings, sex, _tested_genes(record, pack))


async def open_case_for(
    db: AsyncSession, person_id: uuid.UUID, couple_id: uuid.UUID
) -> CareCase | None:
    case: CareCase | None = await db.scalar(
        select(CareCase)
        .where(CareCase.subject_id == person_id, CareCase.couple_id == couple_id)
        .order_by(CareCase.created_at.desc())
        .limit(1)
    )
    return case
