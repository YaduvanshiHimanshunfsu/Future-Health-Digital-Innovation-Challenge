"""Referrals as FHIR R5 resources: a ServiceRequest for the referral, and a Task for its hand-off.

Minimum necessary (V5.2.2). A resource carries what the receiving service needs to act and nothing
else: the kind of service, its status and dates, and who it's for as a pseudonym. Never a name, an
ID number, a gene, a condition or a result; those travel only by the clinical route, with consent.
Every resource is validated by `fhir.resources` before it's returned (V5.2.1).
"""

from datetime import datetime
from typing import Any

from fhir.resources.servicerequest import ServiceRequest
from fhir.resources.task import Task

from app.models.enums import ReferralKind, ReferralStatus
from app.models.referral import Referral

PSEUDONYM_SYSTEM = "urn:samvid:pseudonym"
STAFF_SYSTEM = "urn:samvid:staff"

# What the receiving service is asked to do, in plain words. No code system is claimed until a
# reviewer confirms one (see docs/submission/data_sources.md).
SERVICE_TEXT = {
    ReferralKind.CONFIRMATORY_LAB.value: "Confirmatory genetic testing",
    ReferralKind.REPRODUCTIVE_GENOMICS.value: "Reproductive genetics consultation",
}
_SERVICE_REQUEST_STATUS = {
    ReferralStatus.DRAFT.value: "draft",
    ReferralStatus.SENT.value: "active",
    ReferralStatus.ACCEPTED.value: "active",
    ReferralStatus.DECLINED.value: "revoked",
    ReferralStatus.CANCELLED.value: "revoked",
}
_TASK_STATUS = {
    ReferralStatus.DRAFT.value: "draft",
    ReferralStatus.SENT.value: "requested",
    ReferralStatus.ACCEPTED.value: "accepted",
    ReferralStatus.DECLINED.value: "rejected",
    ReferralStatus.CANCELLED.value: "cancelled",
}
# The agreed list. A snapshot test fails if a field is added without updating it.
SERVICE_REQUEST_FIELDS = frozenset(
    {
        "resourceType",
        "id",
        "status",
        "intent",
        "code",
        "subject",
        "requester",
        "authoredOn",
        "performer",
    }
)
TASK_FIELDS = frozenset(
    {"resourceType", "id", "status", "intent", "focus", "for", "authoredOn", "requester"}
)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def service_request(
    referral: Referral, *, subject_pseudonym: str, requester_pseudonym: str
) -> dict[str, Any]:
    resource = {
        "resourceType": "ServiceRequest",
        "id": str(referral.id),
        "status": _SERVICE_REQUEST_STATUS[referral.status],
        "intent": "order",
        "code": {"concept": {"text": SERVICE_TEXT[referral.kind]}},
        "subject": {"identifier": {"system": PSEUDONYM_SYSTEM, "value": subject_pseudonym}},
        "requester": {"identifier": {"system": STAFF_SYSTEM, "value": requester_pseudonym}},
        "authoredOn": _iso(referral.created_at),
        "performer": [{"display": referral.destination}],
    }
    return ServiceRequest.model_validate(resource).model_dump(mode="json", exclude_none=True)


def task(referral: Referral, *, subject_pseudonym: str, requester_pseudonym: str) -> dict[str, Any]:
    resource = {
        "resourceType": "Task",
        "id": f"{referral.id}-task",
        "status": _TASK_STATUS[referral.status],
        "intent": "order",
        "focus": {"reference": f"ServiceRequest/{referral.id}"},
        "for": {"identifier": {"system": PSEUDONYM_SYSTEM, "value": subject_pseudonym}},
        "authoredOn": _iso(referral.created_at),
        "requester": {"identifier": {"system": STAFF_SYSTEM, "value": requester_pseudonym}},
    }
    return Task.model_validate(resource).model_dump(mode="json", exclude_none=True)
