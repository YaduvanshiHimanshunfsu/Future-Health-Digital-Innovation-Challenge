"""Generates synthetic people, couples and FHIR reports. No real data goes in or comes out.

    uv run python -m synthetic.generate --people 2000

The challenge provides no data, so the demo uses this. Frequencies come from each country pack,
where they're marked as placeholders, so the output shows how the system behaves and says nothing
about any real population.
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import CountryPack, load_pack
from app.ingestion import loinc
from app.risk_engine import rules
from app.risk_engine.engine import couple_assessment, person_facts
from app.risk_engine.types import (
    Classification,
    Finding,
    Inheritance,
    PartnerRecord,
    Relationship,
    Sex,
    Zygosity,
)

PERSONAS_FILE = Path(__file__).parent / "personas.yaml"
DEFAULT_OUTPUT = Path(__file__).parent / "out"
LOINC = "http://loinc.org"
SIGNIFICANCE_CODE = {value: code for code, value in loinc.REPORTABLE.items()}
ZYGOSITY_CODE = {value: code for code, value in loinc.ZYGOSITY.items()}
BENIGN_CODE = "LA6675-8"
# The HL7 security label for test data, so a bundle stays labelled if it's copied somewhere else.
SYNTHETIC_LABEL = {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
    "code": "HTEST",
    "display": "test health data",
}
NOTICE = "Synthetic data for a demo. Not real people. Gene frequencies are placeholders."
GENDER = {Sex.FEMALE: "female", Sex.MALE: "male", Sex.UNKNOWN: "unknown"}
# Illustrative mix, chosen so that every scenario shows up, not to describe any population.
RELATIONSHIP_MIX = (
    (Relationship.UNRELATED, 55),
    (Relationship.SECOND_COUSINS, 15),
    (Relationship.FIRST_COUSINS, 25),
    (Relationship.DOUBLE_FIRST_COUSINS, 5),
)
VUS_SHARE = 0.05


@dataclass(frozen=True, slots=True)
class SyntheticPerson:
    slug: str
    national_id: str
    sex: Sex
    findings: tuple[Finding, ...]
    benign: tuple[tuple[str, str], ...] = ()


def _concept(code: str, *, display: str | None = None, system: str = LOINC) -> dict[str, Any]:
    coding: dict[str, str] = {"system": system, "code": code}
    if display:
        coding["display"] = display
    return {"coding": [coding]}


def _observation(gene: str, variant: str, significance: str, zygosity: str) -> dict[str, Any]:
    def component(code: str, value: dict[str, Any]) -> dict[str, Any]:
        return {"code": _concept(code), "valueCodeableConcept": value}

    return {
        "resourceType": "Observation",
        "status": "final",
        "code": _concept(loinc.VARIANT_ASSESSMENT),
        "component": [
            component(loinc.GENE_STUDIED, _concept(gene, display=gene, system="urn:samvid:gene")),
            component(loinc.DNA_CHANGE_HGVS, _concept(variant, system="http://varnomen.hgvs.org")),
            component(loinc.CLINICAL_SIGNIFICANCE, _concept(significance)),
            component(loinc.ALLELIC_STATE, _concept(zygosity)),
        ],
    }


def build_bundle(
    person: SyntheticPerson,
    pack: CountryPack,
    panel: str,
    *,
    report_id: str | None = None,
    version: int = 1,
    status: str = "final",
) -> dict[str, Any]:
    observations = [
        _observation(
            finding.gene,
            finding.variant,
            SIGNIFICANCE_CODE[finding.classification.value],
            ZYGOSITY_CODE[finding.zygosity.value],
        )
        for finding in person.findings
    ]
    observations += [
        _observation(gene, variant, BENIGN_CODE, ZYGOSITY_CODE["het"])
        for gene, variant in person.benign
    ]
    patient = {
        "resourceType": "Patient",
        "gender": GENDER[person.sex],
        "identifier": [
            {"system": pack.identity.national_id_fhir_system, "value": person.national_id}
        ],
    }
    report = {
        "resourceType": "DiagnosticReport",
        "meta": {"versionId": str(version)},
        "status": status,
        "identifier": [
            {"system": "urn:samvid:demo-lab", "value": report_id or f"DEMO-{person.slug}"}
        ],
        "code": _concept(panel, system="urn:samvid:panel"),
    }
    return {
        "resourceType": "Bundle",
        "meta": {"security": [SYNTHETIC_LABEL]},
        "type": "collection",
        "entry": [{"resource": resource} for resource in (patient, report, *observations)],
    }


def load_personas(pack_code: str) -> tuple[str, dict[str, SyntheticPerson], dict[str, Any]]:
    with PERSONAS_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)[pack_code]
    people = {
        slug: SyntheticPerson(
            slug=slug,
            national_id=entry["id"],
            sex=Sex(entry["sex"]),
            findings=tuple(
                Finding(gene, Classification(cls), Zygosity(zygosity), variant)
                for gene, cls, zygosity, variant in entry["findings"]
            ),
            benign=tuple(tuple(item) for item in entry.get("benign", [])),
        )
        for slug, entry in data["people"].items()
    }
    return data["panel"], people, data["couples"]


def _fake_id(pack: CountryPack, number: int) -> str:
    if pack.code == "ae-abu-dhabi":
        return f"784-0000-{number:07d}-0"
    return f"00-0000-{number // 10000:04d}-{number % 10000:04d}"


def _draw_findings(
    rng: random.Random, pack: CountryPack, sex: Sex, inherited: list[Finding] | None = None
) -> tuple[Finding, ...]:
    findings = list(inherited or [])
    held = {finding.gene for finding in findings}
    for gene in sorted(pack.panel.genes):
        entry = pack.panel.genes[gene]
        if gene in held or rng.random() >= entry.carrier_frequency:
            continue
        on_the_x = entry.inheritance in (
            Inheritance.X_LINKED.value,
            Inheritance.X_LINKED_DOMINANT.value,
        )
        xl_man = on_the_x and sex is Sex.MALE
        classification = (
            Classification.UNCERTAIN
            if rng.random() < VUS_SHARE
            else rng.choice([Classification.PATHOGENIC, Classification.LIKELY_PATHOGENIC])
        )
        findings.append(
            Finding(
                gene,
                classification,
                Zygosity.HEMIZYGOUS if xl_man else Zygosity.HETEROZYGOUS,
                f"c.{rng.randint(1, 2000)}A>G",
            )
        )
    return tuple(findings)


def generate_population(
    pack: CountryPack, panel: str, people: int, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Seeded per pack, so adding a country can't change another country's output.
    rng = random.Random(f"{seed}:{pack.code}")  # noqa: S311  # nosec B311 - synthetic data, not security
    relationships = [item for item, weight in RELATIONSHIP_MIX for _ in range(weight)]
    tested = pack.gene_table.panel(panel)
    couples: list[dict[str, Any]] = []
    scenarios: Counter[str] = Counter()
    founders_holding: Counter[str] = Counter()
    founders = people // 2

    for number in range(founders):
        relationship = rng.choice(relationships)
        a_findings = _draw_findings(rng, pack, Sex.FEMALE)
        for gene in {finding.gene for finding in a_findings}:
            founders_holding[gene] += 1

        kinship = rules.KINSHIP[relationship]
        shared_by_descent = [
            Finding(finding.gene, finding.classification, Zygosity.HETEROZYGOUS, finding.variant)
            for finding in a_findings
            if pack.panel.genes[finding.gene].inheritance == Inheritance.AUTOSOMAL_RECESSIVE.value
            and rng.random() < float(kinship)
        ]
        b_findings = _draw_findings(rng, pack, Sex.MALE, shared_by_descent)

        a = SyntheticPerson(
            f"p{number * 2}", _fake_id(pack, number * 2 + 1000), Sex.FEMALE, a_findings
        )
        b = SyntheticPerson(
            f"p{number * 2 + 1}", _fake_id(pack, number * 2 + 1001), Sex.MALE, b_findings
        )
        for fact in person_facts(a.findings, a.sex, pack.gene_table):
            scenarios[fact.scenario.value] += 1
        for fact in person_facts(b.findings, b.sex, pack.gene_table):
            scenarios[fact.scenario.value] += 1
        assessment = couple_assessment(
            PartnerRecord(a.findings, a.sex, tested),
            PartnerRecord(b.findings, b.sex, tested),
            relationship,
            pack.gene_table,
        )
        for item in assessment.facts:
            scenarios[item.fact.scenario.value] += 1
        couples.append(
            {
                "relationship": relationship.value,
                "a": build_bundle(a, pack, panel),
                "b": build_bundle(b, pack, panel),
            }
        )

    rates = {
        gene: {
            "table": float(Fraction(entry.carrier_frequency).limit_denominator(1_000_000)),
            "observed": round(founders_holding[gene] / founders, 5) if founders else 0.0,
        }
        for gene, entry in sorted(pack.panel.genes.items())
    }
    return couples, {"scenarios": dict(sorted(scenarios.items())), "carrier_rates": rates}


def _persona_scenarios(
    pack: CountryPack, panel: str, people: dict[str, SyntheticPerson], couples: dict[str, Any]
) -> dict[str, int]:
    seen: Counter[str] = Counter()
    tested = pack.gene_table.panel(panel)
    for person in people.values():
        for fact in person_facts(person.findings, person.sex, pack.gene_table):
            seen[fact.scenario.value] += 1
    for couple in couples.values():
        a, b = people[couple["a"]], people[couple["b"]]
        # A partner who hasn't had the panel is a different calculation from one who tested negative.
        b_tested = tested if couple.get("b_tested", True) else None
        assessment = couple_assessment(
            PartnerRecord(a.findings, a.sex, tested),
            PartnerRecord(b.findings, b.sex, b_tested),
            Relationship(couple["relationship"]),
            pack.gene_table,
        )
        for item in assessment.facts:
            seen[item.fact.scenario.value] += 1
    return dict(sorted(seen.items()))


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, sort_keys=True, indent=1, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def generate(
    output: Path, pack_code: str, people: int, seed: int, packs_dir: Path
) -> dict[str, Any]:
    pack = load_pack(packs_dir / pack_code)
    panel, personas, persona_couples = load_personas(pack_code)
    for person in personas.values():
        _dump(
            output / pack_code / "personas" / f"{person.slug}.json",
            build_bundle(person, pack, panel),
        )
    couples, summary = generate_population(pack, panel, people, seed)
    _dump(output / pack_code / "population.json", {"notice": NOTICE, "couples": couples})
    report = {
        "notice": NOTICE,
        "pack": pack_code,
        "seed": seed,
        "people": len(couples) * 2,
        "personas": sorted(personas),
        "persona_scenarios": _persona_scenarios(pack, panel, personas, persona_couples),
        **summary,
    }
    _dump(output / pack_code / "summary.json", report)
    return report


def tree_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--people", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261120)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--packs-dir", type=Path, default=DEFAULT_PACKS_DIR)
    parser.add_argument("--pack", action="append", dest="packs", default=None)
    args = parser.parse_args()
    for pack_code in args.packs or ["ae-abu-dhabi"]:
        report = generate(args.output, pack_code, args.people, args.seed, args.packs_dir)
        sys.stdout.write(f"{pack_code}: {report['people']} people, {report['scenarios']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
