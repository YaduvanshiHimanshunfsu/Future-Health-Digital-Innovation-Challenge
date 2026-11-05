import re
from dataclasses import dataclass
from typing import Any

from fhir.resources.R4B.bundle import Bundle
from pydantic import ValidationError

from app.ingestion import loinc
from app.risk_engine.types import Classification, Finding, Sex, Zygosity

_GENE = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,14}$")
_HGVS = re.compile(r"^[A-Za-z0-9_.:>+\-*()\[\];=]{1,200}$")
_MAX_ENTRIES = 2000
_BUNDLE_TYPES = frozenset({"collection", "document", "transaction", "message"})
_SEX = {"female": Sex.FEMALE, "male": Sex.MALE}
_ACCEPTED_REPORT_STATUS = frozenset({"final", "amended", "corrected"})


class BundleError(ValueError):
    """The bundle can't be trusted. The message names a rule and never quotes the data."""


@dataclass(frozen=True, slots=True)
class ParsedReport:
    national_id: str
    sex: Sex
    report_id: str
    report_version: int
    panel_version: str
    findings: tuple[Finding, ...]

    def __repr__(self) -> str:
        return f"ParsedReport(report_id={self.report_id!r}, findings=<{len(self.findings)}>)"


def _code(concept: Any) -> str | None:
    for coding in (concept or {}).get("coding") or []:
        if coding.get("code"):
            return str(coding["code"])
    return None


def _display(concept: Any) -> str | None:
    for coding in (concept or {}).get("coding") or []:
        if coding.get("display"):
            return str(coding["display"])
    return None


def _finding(observation: dict[str, Any]) -> Finding | None:
    parts = {_code(part.get("code")): part for part in observation.get("component") or []}
    significance = _code(parts.get(loinc.CLINICAL_SIGNIFICANCE, {}).get("valueCodeableConcept"))
    if significance in loinc.NOT_REPORTABLE:
        return None
    if significance not in loinc.REPORTABLE:
        raise BundleError("unrecognised clinical significance")

    gene = (_display(parts.get(loinc.GENE_STUDIED, {}).get("valueCodeableConcept")) or "").upper()
    hgvs = _code(parts.get(loinc.DNA_CHANGE_HGVS, {}).get("valueCodeableConcept")) or ""
    zygosity = loinc.ZYGOSITY.get(
        _code(parts.get(loinc.ALLELIC_STATE, {}).get("valueCodeableConcept")) or ""
    )
    if not (_GENE.fullmatch(gene) and _HGVS.fullmatch(hgvs) and zygosity):
        raise BundleError("invalid variant fields")
    return Finding(
        gene=gene,
        classification=Classification(loinc.REPORTABLE[significance]),
        zygosity=Zygosity(zygosity),
        variant=hgvs,
    )


def parse_report(bundle: Any, *, national_id_system: str) -> ParsedReport:
    """Validate a FHIR R4B bundle and keep only what the service needs: the reportable minimum."""
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise BundleError("not a Bundle")
    if bundle.get("type") not in _BUNDLE_TYPES:
        raise BundleError("unsupported Bundle type")
    entries = bundle.get("entry")
    if not isinstance(entries, list) or not 0 < len(entries) <= _MAX_ENTRIES:
        raise BundleError("bad entry list")
    try:
        Bundle.model_validate(bundle)
    except ValidationError:
        # Not chained: pydantic's message can quote values from the bundle.
        raise BundleError("not valid FHIR") from None

    resources = [entry.get("resource") or {} for entry in entries]
    patients = [res for res in resources if res.get("resourceType") == "Patient"]
    reports = [res for res in resources if res.get("resourceType") == "DiagnosticReport"]
    if len(patients) != 1 or len(reports) != 1:
        raise BundleError("expected exactly one Patient and one DiagnosticReport")
    patient, report = patients[0], reports[0]

    national_id = next(
        (
            str(identifier["value"])
            for identifier in patient.get("identifier") or []
            if identifier.get("system") == national_id_system and identifier.get("value")
        ),
        None,
    )
    if not national_id:
        raise BundleError("no patient identifier for this country")

    if report.get("status") not in _ACCEPTED_REPORT_STATUS:
        raise BundleError("report isn't final")
    report_ids = report.get("identifier") or []
    report_id = str(report_ids[0].get("value") or "") if report_ids else ""
    panel_version = _code(report.get("code")) or ""
    if not (0 < len(report_id) <= 128 and 0 < len(panel_version) <= 32):
        raise BundleError("report identifier or panel missing")
    version_text = str((report.get("meta") or {}).get("versionId") or "1")
    if not version_text.isascii() or not version_text.isdigit() or int(version_text) < 1:
        raise BundleError("invalid report version")

    findings = []
    for resource in resources:
        if (
            resource.get("resourceType") == "Observation"
            and _code(resource.get("code")) == loinc.VARIANT_ASSESSMENT
        ):
            finding = _finding(resource)
            if finding:
                findings.append(finding)

    return ParsedReport(
        national_id=national_id,
        sex=_SEX.get(str(patient.get("gender")), Sex.UNKNOWN),
        report_id=report_id,
        report_version=int(version_text),
        panel_version=panel_version,
        findings=tuple(findings),
    )
