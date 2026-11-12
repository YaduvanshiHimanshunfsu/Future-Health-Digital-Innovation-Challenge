from enum import StrEnum

from sqlalchemy import CheckConstraint


class Attestation(StrEnum):
    """How far a lab report can be trusted. Couple matching reads only trusted reports."""

    VERIFIED = "verified"
    DEMO = "demo"
    UNVERIFIED = "unverified"


class ConsentKind(StrEnum):
    SERVICE = "service"
    COUPLE_MATCH = "couple_match"
    SHARE_SUMMARY = "share_summary"
    SHARE_FULL = "share_full"
    RESEARCH = "research"


class RevealLevel(StrEnum):
    YES_NO = "yes_no"
    GENES = "genes"


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class CaseState(StrEnum):
    RESULT_RELEASED = "RESULT_RELEASED"
    EDUCATION_VIEWED = "EDUCATION_VIEWED"
    COMPREHENSION_CHECKED = "COMPREHENSION_CHECKED"
    COUNSELLING_REQUESTED = "COUNSELLING_REQUESTED"
    COUNSELLING_BOOKED = "COUNSELLING_BOOKED"
    COUNSELLING_DONE = "COUNSELLING_DONE"
    CONFIRMATORY_TEST_ORDERED = "CONFIRMATORY_TEST_ORDERED"
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    REPRO_GENOMICS_REFERRED = "REPRO_GENOMICS_REFERRED"
    REFERRAL_ACCEPTED = "REFERRAL_ACCEPTED"
    DECLINED_BY_USER = "DECLINED_BY_USER"
    LOST_TO_FOLLOW_UP = "LOST_TO_FOLLOW_UP"
    CLOSED = "CLOSED"


class Boundary(StrEnum):
    EDUCATION = "EDUCATION"
    DECISION_SUPPORT = "DECISION_SUPPORT"
    CLINICAL_ADVICE = "CLINICAL_ADVICE"
    DISTRESS = "DISTRESS"
    COERCION = "COERCION"


class AnswerSource(StrEnum):
    LLM = "llm"
    TEMPLATE = "template"


class ReadingLevel(StrEnum):
    SIMPLE = "simple"
    STANDARD = "standard"
    DETAILED = "detailed"


class Instrument(StrEnum):
    TEACH_BACK = "teach_back"
    MMIC_ADAPTED = "mmic_adapted"
    SURE = "sure"
    GCOS = "gcos"


class AssessmentPhase(StrEnum):
    PRE = "pre"
    POST = "post"


class AppointmentStatus(StrEnum):
    OPEN = "open"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class AppointmentMode(StrEnum):
    IN_PERSON = "in_person"
    VIDEO = "video"


class ReferralKind(StrEnum):
    CONFIRMATORY_LAB = "confirmatory_lab"
    REPRODUCTIVE_GENOMICS = "reproductive_genomics"


class ReferralStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"


class OutboxOperation(StrEnum):
    WRITE = "write"
    DELETE = "delete"


def one_of(column: str, enum: type[StrEnum], *, name: str | None = None) -> CheckConstraint:
    allowed = ", ".join(f"'{member.value}'" for member in enum)
    return CheckConstraint(f"{column} IN ({allowed})", name=name or column)
