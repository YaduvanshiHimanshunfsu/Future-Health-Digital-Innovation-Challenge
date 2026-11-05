from fractions import Fraction

import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.models.enums import Priority
from app.risk_engine.engine import _fact, couple_assessment, partner_view, person_facts
from app.risk_engine.types import Flag, Label, PartnerRecord, Relationship, Reveal, Scenario, Viewer
from app.triage.scoring import score
from synthetic.generate import load_personas

PACK = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
PANEL, PEOPLE, COUPLES = load_personas("ae-abu-dhabi")


@pytest.mark.parametrize(
    ("persona", "priority", "reason"),
    [
        ("x_man", Priority.P1, "possibly_affected"),
        ("two_variants", Priority.P1, "possibly_affected"),
        ("two_copies", Priority.P1, "possibly_affected"),
        ("x_two_copies", Priority.P1, "possibly_affected"),
        ("x_carrier", Priority.P2, "x_linked_carrier"),
        ("uncertain", Priority.P3, "uncertain_finding"),
        ("g6pd_man", Priority.P3, "possibly_affected_routine"),
        ("gene_not_in_pack", Priority.P3, "needs_clinical_check"),
    ],
)
def test_each_persona_gets_the_right_priority(
    persona: str, priority: Priority, reason: str
) -> None:
    """V4.5.1, early: person-level rules."""
    person = PEOPLE[persona]
    result = score(person_facts(person.findings, person.sex, PACK.gene_table))
    assert result is not None
    assert result.priority is priority
    assert reason in result.reasons


@pytest.mark.parametrize("persona", ["fatima", "no_findings"])
def test_ordinary_results_raise_no_trigger(persona: str) -> None:
    person = PEOPLE[persona]
    assert score(person_facts(person.findings, person.sex, PACK.gene_table)) is None


def _couple_facts(name: str) -> list:
    couple = COUPLES[name]
    a, b = PEOPLE[couple["a"]], PEOPLE[couple["b"]]
    tested = PACK.gene_table.panel(PANEL)
    assessment = couple_assessment(
        PartnerRecord(a.findings, a.sex, tested),
        PartnerRecord(b.findings, b.sex, tested),
        Relationship(couple["relationship"]),
        PACK.gene_table,
    )
    return partner_view(assessment, Viewer.A, Reveal.GENES)


@pytest.mark.parametrize(
    ("couple", "reason"),
    [
        ("at_risk", "shared_finding"),
        ("alpha_pair", "couple_review"),
        ("x_couple", "x_linked_couple"),
    ],
)
def test_couples_needing_a_counsellor_get_p2(couple: str, reason: str) -> None:
    result = score(_couple_facts(couple))
    assert result is not None
    assert result.priority is Priority.P2
    assert reason in result.reasons


def test_several_shared_genes_are_noted() -> None:
    facts = [
        _fact(
            Scenario.COUPLE_SHARED_AR, gene, Label.TWO_COPIES, Fraction(1, 4), "c", Flag.SHARED_AR
        )
        for gene in ("HBB", "SMN1")
    ]
    result = score(facts)
    assert result is not None
    assert "several_shared_findings" in result.reasons


def test_distress_is_always_urgent() -> None:
    result = score([], distress=True)
    assert result is not None
    assert result.priority is Priority.P1


def test_pregnancy_with_a_shared_finding_is_urgent() -> None:
    result = score(_couple_facts("at_risk"), pregnant=True)
    assert result is not None
    assert result.priority is Priority.P1
    assert "pregnant_with_finding" in result.reasons


def test_pregnancy_alone_raises_nothing() -> None:
    assert score([], pregnant=True) is None


def test_failing_the_check_twice_offers_support() -> None:
    assert score([], teach_back_failures=1) is None
    result = score([], teach_back_failures=2)
    assert result is not None
    assert result.priority is Priority.P3


def test_related_couple_asking_about_extended_testing() -> None:
    background = [
        _fact(
            Scenario.CONSANGUINITY_BACKGROUND,
            None,
            Label.BACKGROUND,
            None,
            "c",
            Flag.CONSANGUINEOUS,
        )
    ]
    assert score(background) is None
    result = score(background, asked_about_extended_testing=True)
    assert result is not None
    assert result.priority is Priority.P3


def test_asking_for_a_person_always_gets_a_case() -> None:
    result = score([], asked_for_human=True)
    assert result is not None
    assert result.priority is Priority.P4


def test_highest_priority_wins() -> None:
    result = score(_couple_facts("at_risk"), distress=True, asked_for_human=True)
    assert result is not None
    assert result.priority is Priority.P1
