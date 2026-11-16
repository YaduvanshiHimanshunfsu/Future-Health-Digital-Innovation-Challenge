"""Expected values in the tables here were worked out by hand from Mendelian inheritance, not read
back from the code. See docs/clinical/risk_rules_review.md for the rule table they come from."""

from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.risk_engine import rules
from app.risk_engine.engine import couple_assessment, partner_view, person_facts
from app.risk_engine.frequencies import GeneInfo, GeneTable
from app.risk_engine.types import (
    Classification,
    CoupleAssessment,
    Finding,
    Flag,
    Inheritance,
    Label,
    PartnerRecord,
    Relationship,
    Reveal,
    RiskFact,
    Scenario,
    Sex,
    Viewer,
    Zygosity,
)

P = Classification.PATHOGENIC
LP = Classification.LIKELY_PATHOGENIC
VUS = Classification.UNCERTAIN
HET, HOM, HEMI = Zygosity.HETEROZYGOUS, Zygosity.HOMOZYGOUS, Zygosity.HEMIZYGOUS
Q = Fraction(1, 20)
D = Fraction(49, 50)


def gene(
    name: str,
    inheritance: Inheritance = Inheritance.AUTOSOMAL_RECESSIVE,
    risk_group: str | None = None,
    routine: bool = False,
) -> GeneInfo:
    return GeneInfo(name, inheritance, Q, D, risk_group=risk_group, routine_when_hemizygous=routine)


TABLE = GeneTable(
    {
        info.gene: info
        for info in (
            gene("HBB"),
            gene("SMN1"),
            gene("CYP21A2"),
            gene("HBA1", risk_group="alpha_thalassaemia"),
            gene("HBA2", risk_group="alpha_thalassaemia"),
            gene("DMD", Inheritance.X_LINKED),
            gene("G6PD", Inheritance.X_LINKED, routine=True),
            gene("LDLR", Inheritance.AUTOSOMAL_DOMINANT),
            gene("PHEX", Inheritance.X_LINKED_DOMINANT),
        )
    }
)
PANEL = TABLE.genes


def finding(
    name: str, cls: Classification = P, zyg: Zygosity = HET, variant: str = "c.1"
) -> Finding:
    return Finding(name, cls, zyg, variant)


def record(
    *findings: Finding, sex: Sex = Sex.FEMALE, tested: frozenset[str] | None = PANEL
) -> PartnerRecord:
    return PartnerRecord(tuple(findings), sex, tested)


def values(facts: list[RiskFact], name: str | None = None) -> dict[Label, Fraction | None]:
    return {fact.label: fact.value for fact in facts if name is None or fact.gene == name}


def view(
    a: PartnerRecord,
    b: PartnerRecord,
    who: Viewer,
    *,
    relationship: Relationship = Relationship.UNRELATED,
    reveal: Reveal = Reveal.GENES,
) -> list[RiskFact]:
    return partner_view(couple_assessment(a, b, relationship, TABLE), who, reveal)


class TestPersonFacts:
    def test_one_changed_copy_is_a_carrier_with_no_number(self) -> None:
        facts = person_facts([finding("HBB")], Sex.FEMALE, TABLE)
        assert [fact.scenario for fact in facts] == [Scenario.CARRIER_SELF]
        assert facts[0].value is None

    def test_likely_pathogenic_counts_as_pathogenic(self) -> None:
        facts = person_facts([finding("HBB", LP)], Sex.MALE, TABLE)
        assert facts[0].scenario is Scenario.CARRIER_SELF

    def test_homozygous_is_possibly_affected_not_carrier(self) -> None:
        fact = person_facts([finding("HBB", zyg=HOM)], Sex.FEMALE, TABLE)[0]
        assert fact.scenario is Scenario.POSSIBLE_AFFECTED
        assert fact.value is None
        assert Flag.POSSIBLE_AFFECTED in fact.flags

    def test_two_variants_in_one_gene_escalate(self) -> None:
        """V2.4.3. The original spec reported this as two separate carrier facts."""
        facts = person_facts(
            [finding("HBB", variant="c.1"), finding("HBB", LP, variant="c.2")], Sex.FEMALE, TABLE
        )
        assert [fact.scenario for fact in facts] == [Scenario.POSSIBLE_AFFECTED]

    def test_the_same_variant_reported_twice_is_still_one_copy(self) -> None:
        facts = person_facts([finding("HBB"), finding("HBB")], Sex.FEMALE, TABLE)
        assert facts[0].scenario is Scenario.CARRIER_SELF

    def test_hemizygous_man_is_never_called_a_carrier(self) -> None:
        """V2.4.1. The original spec returned carrier_self here."""
        facts = person_facts([finding("DMD", zyg=HEMI)], Sex.MALE, TABLE)
        assert [fact.scenario for fact in facts] == [Scenario.POSSIBLE_AFFECTED]
        assert all(fact.label is not Label.CARRIER for fact in facts)
        assert Flag.POSSIBLE_AFFECTED in facts[0].flags

    def test_common_x_linked_condition_is_not_urgent_in_men(self) -> None:
        fact = person_facts([finding("G6PD", zyg=HEMI)], Sex.MALE, TABLE)[0]
        assert Flag.POSSIBLE_AFFECTED_ROUTINE in fact.flags
        assert Flag.POSSIBLE_AFFECTED not in fact.flags

    def test_x_linked_carrier_woman(self) -> None:
        facts = person_facts([finding("DMD")], Sex.FEMALE, TABLE)
        assert values(facts) == {
            Label.SON_AFFECTED: Fraction(1, 2),
            Label.DAUGHTER_CARRIER: Fraction(1, 2),
        }
        assert all(Flag.XL_FEMALE in fact.flags for fact in facts)

    def test_homozygous_x_linked_woman_passes_it_to_every_son_and_escalates(self) -> None:
        """V2.4.13. The original spec gave sons 1/2."""
        facts = person_facts([finding("DMD", zyg=HOM)], Sex.FEMALE, TABLE)
        assert values(facts)[Label.SON_AFFECTED] == 1
        assert values(facts)[Label.DAUGHTER_CARRIER] == 1
        assert any(Flag.POSSIBLE_AFFECTED in fact.flags for fact in facts)

    @pytest.mark.parametrize(
        ("name", "zyg", "sex"),
        [
            ("DMD", HET, Sex.MALE),
            ("DMD", HOM, Sex.MALE),
            ("DMD", HEMI, Sex.FEMALE),
            ("DMD", HET, Sex.UNKNOWN),
            ("HBB", HEMI, Sex.FEMALE),
        ],
    )
    def test_impossible_combinations_are_referred_without_a_number(
        self, name: str, zyg: Zygosity, sex: Sex
    ) -> None:
        fact = person_facts([finding(name, zyg=zyg)], sex, TABLE)[0]
        assert fact.scenario is Scenario.REFER
        assert fact.value is None
        assert Flag.INCONSISTENT_DATA in fact.flags

    def test_unknown_gene_is_referred_without_a_crash(self) -> None:
        """V2.4.5. The original spec raised KeyError."""
        fact = person_facts([finding("NOTINPACK")], Sex.FEMALE, TABLE)[0]
        assert fact.scenario is Scenario.REFER
        assert fact.value is None
        assert Flag.UNKNOWN_GENE in fact.flags

    def test_vus_gives_no_number(self) -> None:
        fact = person_facts([finding("HBB", VUS)], Sex.FEMALE, TABLE)[0]
        assert fact.scenario is Scenario.UNCERTAIN_VUS
        assert fact.value is None

    def test_vus_beside_a_pathogenic_finding_still_gives_no_number(self) -> None:
        for order in (
            [finding("HBB", VUS, variant="v"), finding("HBB")],
            [finding("HBB"), finding("HBB", VUS, variant="v")],
        ):
            facts = person_facts(order, Sex.FEMALE, TABLE)
            assert [fact.scenario for fact in facts] == [Scenario.UNCERTAIN_VUS]

    def test_no_findings_means_no_facts(self) -> None:
        assert person_facts([], Sex.FEMALE, TABLE) == []


class TestSharedRecessive:
    @pytest.mark.parametrize(
        ("a_zyg", "b_zyg", "two", "carrier", "neither"),
        [
            (HET, HET, Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)),
            (HOM, HET, Fraction(1, 2), Fraction(1, 2), Fraction(0)),
            (HET, HOM, Fraction(1, 2), Fraction(1, 2), Fraction(0)),
            (HOM, HOM, Fraction(1), Fraction(0), Fraction(0)),
        ],
    )
    def test_outcomes_follow_what_each_parent_can_pass_on(
        self, a_zyg: Zygosity, b_zyg: Zygosity, two: Fraction, carrier: Fraction, neither: Fraction
    ) -> None:
        """V2.4.2. The original spec gave 1/4 whatever the zygosity."""
        facts = view(
            record(finding("HBB", zyg=a_zyg)),
            record(finding("HBB", zyg=b_zyg), sex=Sex.MALE),
            Viewer.A,
        )
        assert values(facts) == {
            Label.TWO_COPIES: two,
            Label.CARRIER: carrier,
            Label.NEITHER: neither,
        }

    def test_compound_parent_behaves_like_a_homozygous_parent(self) -> None:
        compound = record(finding("HBB", variant="c.1"), finding("HBB", variant="c.2"))
        facts = view(compound, record(finding("HBB"), sex=Sex.MALE), Viewer.A)
        assert values(facts)[Label.TWO_COPIES] == Fraction(1, 2)

    def test_recorded_as_shared_with_flag(self) -> None:
        assessment = couple_assessment(
            record(finding("HBB")), record(finding("HBB")), Relationship.UNRELATED, TABLE
        )
        assert assessment.shared_genes == {"HBB"}
        assert assessment.any_shared
        assert all(Flag.SHARED_AR in item.fact.flags for item in assessment.facts)

    def test_different_genes_are_not_shared(self) -> None:
        assessment = couple_assessment(
            record(finding("HBB")), record(finding("SMN1")), Relationship.UNRELATED, TABLE
        )
        assert not assessment.any_shared


class TestOneCarrier:
    def test_partner_tested_negative_uses_bayes(self) -> None:
        # q = 1/20, d = 49/50: residual = (1/20)(1/50) / (1 - 49/1000) = 1/951. Child: that over 4.
        facts = view(record(finding("HBB")), record(), Viewer.A)
        fact = facts[0]
        assert fact.scenario is Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE
        assert fact.value == Fraction(1, 951) / 4

    def test_first_cousins_use_the_kinship_prior_after_a_negative_test(self) -> None:
        """V2.4.6. The original spec gave cousins the same figure as unrelated couples."""
        # prior = 1/8 + (7/8)(1/20) = 27/160. residual = prior(1/50) / (1 - prior(49/50)).
        prior = Fraction(27, 160)
        expected = prior * Fraction(1, 50) / (1 - prior * D) / 4
        facts = view(
            record(finding("HBB")), record(), Viewer.A, relationship=Relationship.FIRST_COUSINS
        )
        assert facts[0].value == expected

    def test_untested_partner_uses_the_prior(self) -> None:
        facts = view(record(finding("HBB")), record(tested=None), Viewer.A)
        assert facts[0].scenario is Scenario.COUPLE_ONE_CARRIER_UNTESTED
        assert facts[0].value == Q / 4

    def test_gene_outside_the_partners_panel_counts_as_untested(self) -> None:
        facts = view(record(finding("HBB")), record(tested=frozenset({"SMN1"})), Viewer.A)
        assert facts[0].scenario is Scenario.COUPLE_ONE_CARRIER_UNTESTED

    def test_homozygous_holder_doubles_the_chance(self) -> None:
        facts = view(record(finding("HBB", zyg=HOM)), record(tested=None), Viewer.A)
        assert facts[0].value == Q / 2

    @given(
        q=st.fractions(min_value=Fraction(1, 100_000), max_value=Fraction(1, 5)),
        d=st.fractions(min_value=Fraction(1, 2), max_value=Fraction(99, 100)),
        relationship=st.sampled_from(
            [
                Relationship.DOUBLE_FIRST_COUSINS,
                Relationship.FIRST_COUSINS,
                Relationship.FIRST_COUSINS_ONCE_REMOVED,
                Relationship.SECOND_COUSINS,
            ]
        ),
    )
    def test_relatives_always_have_a_higher_residual_than_unrelated_couples(
        self, q: Fraction, d: Fraction, relationship: Relationship
    ) -> None:
        unrelated = rules.residual_after_negative(rules.carrier_prior(q, Relationship.UNRELATED), d)
        related = rules.residual_after_negative(rules.carrier_prior(q, relationship), d)
        assert related > unrelated

    @given(
        prior=st.fractions(min_value=Fraction(0), max_value=Fraction(9, 10)),
        d=st.fractions(min_value=Fraction(0), max_value=Fraction(1)),
    )
    def test_a_negative_test_never_raises_the_chance(self, prior: Fraction, d: Fraction) -> None:
        assert 0 <= rules.residual_after_negative(prior, d) <= prior

    @pytest.mark.parametrize(
        ("prior", "d"),
        [
            (Fraction(1), Fraction(1, 2)),
            (Fraction(-1, 2), Fraction(1, 2)),
            (Fraction(1, 2), Fraction(3, 2)),
        ],
    )
    def test_impossible_inputs_are_refused(self, prior: Fraction, d: Fraction) -> None:
        with pytest.raises(ValueError, match="prior"):
            rules.residual_after_negative(prior, d)

    @pytest.mark.parametrize(
        ("relationship", "r"),
        [
            (Relationship.DOUBLE_FIRST_COUSINS, Fraction(1, 4)),
            (Relationship.FIRST_COUSINS, Fraction(1, 8)),
            (Relationship.FIRST_COUSINS_ONCE_REMOVED, Fraction(1, 16)),
            (Relationship.SECOND_COUSINS, Fraction(1, 32)),
            (Relationship.UNRELATED, Fraction(0)),
            (Relationship.UNKNOWN, Fraction(0)),
        ],
    )
    def test_coefficients(self, relationship: Relationship, r: Fraction) -> None:
        assert rules.KINSHIP[relationship] == r


class TestUncertainty:
    def test_vus_in_one_partner_blocks_any_number_for_both(self) -> None:
        a, b = record(finding("HBB", VUS)), record(finding("HBB"), sex=Sex.MALE)
        for who in Viewer:
            facts = view(a, b, who)
            assert [fact.scenario for fact in facts] == [Scenario.COUPLE_REVIEW]
            assert facts[0].value is None
        assert Flag.VUS in view(a, b, Viewer.A)[0].flags

    def test_vus_mixed_with_pathogenic_gives_no_number(self) -> None:
        """The original spec's dict kept only the last finding and produced 25% here."""
        a = record(finding("HBB", VUS, variant="v"), finding("HBB"))
        facts = view(a, record(finding("HBB"), sex=Sex.MALE), Viewer.A)
        assert all(fact.value is None for fact in facts)

    def test_one_partners_lone_vus_stays_with_them(self) -> None:
        a, b = record(finding("HBB", VUS)), record(sex=Sex.MALE)
        assert [fact.scenario for fact in view(a, b, Viewer.A)] == [Scenario.UNCERTAIN_VUS]
        assert view(a, b, Viewer.B) == []

    def test_inconsistent_partner_data_blocks_the_number(self) -> None:
        a, b = record(finding("HBB", zyg=HEMI)), record(finding("HBB"), sex=Sex.MALE)
        assert all(fact.value is None for fact in view(a, b, Viewer.A))

    def test_gene_outside_the_pack_goes_to_the_holder_only(self) -> None:
        a, b = record(finding("NOTINPACK")), record(sex=Sex.MALE)
        assert [fact.scenario for fact in view(a, b, Viewer.A)] == [Scenario.REFER]
        assert view(a, b, Viewer.B) == []

    def test_shared_gene_outside_the_pack_still_counts_as_shared(self) -> None:
        assessment = couple_assessment(
            record(finding("NOTINPACK")),
            record(finding("NOTINPACK")),
            Relationship.UNRELATED,
            TABLE,
        )
        assert assessment.shared_genes == {"NOTINPACK"}
        assert all(item.fact.value is None for item in assessment.facts)


class TestRiskGroups:
    def test_different_genes_in_one_group_need_review(self) -> None:
        """V2.4.8. Plain gene matching missed this, and could have falsely reassured the couple."""
        assessment = couple_assessment(
            record(finding("HBA1")),
            record(finding("HBA2"), sex=Sex.MALE),
            Relationship.UNRELATED,
            TABLE,
        )
        assert assessment.review_needed
        assert assessment.any_shared
        facts = partner_view(assessment, Viewer.A, Reveal.GENES)
        assert [fact.scenario for fact in facts] == [Scenario.COUPLE_REVIEW]
        assert facts[0].value is None
        assert facts[0].gene is None
        assert "HBA2" not in facts[0].id

    def test_same_gene_in_a_group_is_a_normal_shared_finding(self) -> None:
        facts = view(record(finding("HBA1")), record(finding("HBA1")), Viewer.A)
        assert values(facts)[Label.TWO_COPIES] == Fraction(1, 4)


class TestXLinkedCouples:
    def test_carrier_mother_and_unaffected_father(self) -> None:
        mother, father = record(finding("DMD")), record(sex=Sex.MALE)
        facts = view(mother, father, Viewer.A)
        assert values(facts) == {
            Label.SON_AFFECTED: Fraction(1, 2),
            Label.DAUGHTER_CARRIER: Fraction(1, 2),
        }
        assert view(mother, father, Viewer.B) == []

    def test_father_with_x_linked_finding_and_mother_without(self) -> None:
        """V2.4.15. Every daughter inherits his X, and no son does."""
        mother, father = record(), record(finding("DMD", zyg=HEMI), sex=Sex.MALE)
        facts = view(mother, father, Viewer.B)
        assert values(facts) == {
            Label.DAUGHTER_CARRIER: Fraction(1),
            Label.SON_AFFECTED: Fraction(0),
        }
        assert view(mother, father, Viewer.A) == []

    def test_both_parents_have_a_finding(self) -> None:
        mother, father = record(finding("DMD")), record(finding("DMD", zyg=HEMI), sex=Sex.MALE)
        assert values(view(mother, father, Viewer.A)) == {
            Label.SON_AFFECTED: Fraction(1, 2),
            Label.DAUGHTER_TWO_COPIES: Fraction(1, 2),
            Label.DAUGHTER_CARRIER: Fraction(1, 2),
            Label.DAUGHTER_NEITHER: Fraction(0),
        }

    def test_works_with_partners_listed_either_way_round(self) -> None:
        father, mother = record(finding("DMD", zyg=HEMI), sex=Sex.MALE), record(finding("DMD"))
        assert values(view(father, mother, Viewer.A))[Label.DAUGHTER_TWO_COPIES] == Fraction(1, 2)

    def test_homozygous_mother_with_affected_father(self) -> None:
        mother, father = (
            record(finding("DMD", zyg=HOM)),
            record(finding("DMD", zyg=HEMI), sex=Sex.MALE),
        )
        assert values(view(mother, father, Viewer.A))[Label.DAUGHTER_TWO_COPIES] == 1

    def test_x_linked_never_uses_recessive_numbers(self) -> None:
        mother, father = record(finding("DMD")), record(finding("DMD", zyg=HEMI), sex=Sex.MALE)
        assert all(fact.label is not Label.TWO_COPIES for fact in view(mother, father, Viewer.A))

    def test_sex_not_a_mother_and_father_pair_is_referred(self) -> None:
        a, b = record(finding("DMD")), record(finding("DMD"))
        facts = view(a, b, Viewer.A)
        assert [fact.scenario for fact in facts] == [Scenario.REFER]
        assert facts[0].value is None

    def test_sex_mismatch_shows_only_to_the_holder(self) -> None:
        a, b = record(finding("DMD")), record()
        assert [fact.scenario for fact in view(a, b, Viewer.A)] == [Scenario.REFER]
        assert view(a, b, Viewer.B) == []
        # Same check with the holder listed second.
        assert [fact.scenario for fact in view(b, a, Viewer.B)] == [Scenario.REFER]


class TestConsanguinity:
    def test_related_couple_with_no_shared_finding_gets_no_figure(self) -> None:
        """V2.4.14. The 1.7-2.8% range describes unscreened couples, not a negative panel."""
        facts = view(
            record(), record(sex=Sex.MALE), Viewer.A, relationship=Relationship.FIRST_COUSINS
        )
        assert [fact.scenario for fact in facts] == [Scenario.CONSANGUINITY_BACKGROUND]
        assert facts[0].value is None
        assert Flag.CONSANGUINEOUS in facts[0].flags

    def test_unrelated_couple_gets_no_background_fact(self) -> None:
        assert view(record(), record(sex=Sex.MALE), Viewer.A) == []

    def test_second_cousins_count(self) -> None:
        facts = view(
            record(), record(sex=Sex.MALE), Viewer.A, relationship=Relationship.SECOND_COUSINS
        )
        assert facts[0].scenario is Scenario.CONSANGUINITY_BACKGROUND

    def test_shared_finding_replaces_the_background_fact(self) -> None:
        facts = view(
            record(finding("HBB")),
            record(finding("HBB"), sex=Sex.MALE),
            Viewer.A,
            relationship=Relationship.FIRST_COUSINS,
        )
        assert all(fact.scenario is not Scenario.CONSANGUINITY_BACKGROUND for fact in facts)


class TestPartnerView:
    def test_partner_only_finding_is_invisible(self) -> None:
        """The original spec's fact IDs named the partner's private gene (C7)."""
        a, b = record(), record(finding("SMN1"), sex=Sex.MALE)
        for reveal in Reveal:
            assert "SMN1" not in repr(view(a, b, Viewer.A, reveal=reveal))

    def test_yes_no_hides_the_shared_gene_everywhere(self) -> None:
        facts = view(record(finding("HBB")), record(finding("HBB")), Viewer.A, reveal=Reveal.YES_NO)
        assert facts
        assert "HBB" not in repr(facts)
        assert all(fact.gene is None for fact in facts)
        assert values(facts)[Label.TWO_COPIES] == Fraction(1, 4)

    def test_yes_no_doesnt_identify_the_gene_by_elimination(self) -> None:
        a = record(finding("HBB"), finding("SMN1"))
        b = record(finding("SMN1"), sex=Sex.MALE)
        assert "HBB" not in repr(view(a, b, Viewer.A, reveal=Reveal.YES_NO))
        assert "SMN1" not in repr(view(a, b, Viewer.A, reveal=Reveal.YES_NO))

    def test_two_shared_genes_stay_distinct_under_yes_no(self) -> None:
        a = record(finding("HBB"), finding("SMN1"))
        b = record(finding("HBB"), finding("SMN1"), sex=Sex.MALE)
        facts = view(a, b, Viewer.A, reveal=Reveal.YES_NO)
        assert len({fact.id for fact in facts}) == 6

    def test_review_without_a_gene_passes_through_yes_no(self) -> None:
        facts = view(
            record(finding("HBA1")), record(finding("HBA2")), Viewer.A, reveal=Reveal.YES_NO
        )
        assert [fact.scenario for fact in facts] == [Scenario.COUPLE_REVIEW]

    def test_assessment_cannot_leak_through_repr(self) -> None:
        assessment = couple_assessment(
            record(finding("HBB")), record(finding("SMN1")), Relationship.UNRELATED, TABLE
        )
        assert "SMN1" not in repr(assessment)
        assert "HBB" not in str(assessment)


class TestYesOrNoHidesPrivateFacts:
    """Seeing which of your own genes has a residual figure would show which one was shared."""

    def assessment(self) -> CoupleAssessment:
        return couple_assessment(
            record(finding("HBB"), finding("SMN1")),
            record(finding("HBB")),
            Relationship.UNRELATED,
            TABLE,
        )

    def test_the_gene_level_view_does_show_the_private_residual(self) -> None:
        """Proves the fixture holds a private fact, so the test below can't pass by default."""
        facts = partner_view(self.assessment(), Viewer.A, Reveal.GENES)
        assert Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE in {fact.scenario for fact in facts}

    def test_the_yes_or_no_view_holds_only_shared_facts(self) -> None:
        facts = partner_view(self.assessment(), Viewer.A, Reveal.YES_NO)
        assert {fact.scenario for fact in facts} == {Scenario.COUPLE_SHARED_AR}


class TestFactFormatting:
    @pytest.mark.parametrize(
        ("value", "percent", "one_in"),
        [
            (Fraction(1, 4), "25", 4),
            (Fraction(1, 2), "50", 2),
            (Fraction(1), "100", 1),
            (Fraction(0), "0", None),
            (Fraction(1, 3804), "0.026", 3804),
        ],
    )
    def test_percent_and_one_in(self, value: Fraction, percent: str, one_in: int | None) -> None:
        fact = RiskFact("x", Scenario.REFER, None, Label.REFER, value, "c", "v")
        assert fact.percent == percent
        assert fact.one_in == one_in
        assert fact.has_number

    def test_no_value_means_no_number_of_any_kind(self) -> None:
        fact = RiskFact("x", Scenario.REFER, None, Label.REFER, None, "c", "v")
        assert fact.percent is None
        assert fact.one_in is None
        assert not fact.has_number

    def test_every_fact_records_its_source_and_rule_version(self) -> None:
        for fact in view(record(finding("HBB")), record(finding("HBB")), Viewer.A):
            assert fact.citation
            assert fact.rule_version


# ---- properties that must hold for any input ----

GENES = ["HBB", "SMN1", "HBA1", "HBA2", "DMD", "G6PD", "NOTINPACK"]
findings_strategy = st.lists(
    st.builds(
        Finding,
        st.sampled_from(GENES),
        st.sampled_from(list(Classification)),
        st.sampled_from(list(Zygosity)),
        st.sampled_from(["c.1", "c.2"]),
    ),
    max_size=5,
)
records_strategy = st.builds(
    PartnerRecord,
    findings_strategy.map(tuple),
    st.sampled_from(list(Sex)),
    st.sampled_from([PANEL, None, frozenset({"HBB"})]),
)
relationships_strategy = st.sampled_from(list(Relationship))


@given(records_strategy, records_strategy, relationships_strategy)
def test_any_vus_means_no_number_for_that_gene(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship
) -> None:
    """V2.4.4."""
    vus_genes = {f.gene for f in a.findings + b.findings if f.classification is VUS}
    assessment = couple_assessment(a, b, relationship, TABLE)
    for item in assessment.facts:
        if item.fact.gene in vus_genes:
            assert item.fact.value is None
    for record_ in (a, b):
        for fact in person_facts(record_.findings, record_.sex, TABLE):
            if fact.gene in {f.gene for f in record_.findings if f.classification is VUS}:
                assert fact.value is None


@given(records_strategy, records_strategy, relationships_strategy)
def test_every_number_is_a_valid_probability(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship
) -> None:
    for item in couple_assessment(a, b, relationship, TABLE).facts:
        if item.fact.value is not None:
            assert 0 <= item.fact.value <= 1


@given(records_strategy, records_strategy, relationships_strategy)
def test_shared_recessive_outcomes_sum_to_one(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship
) -> None:
    """V2.4.7."""
    by_gene: dict[str | None, Fraction] = {}
    for item in couple_assessment(a, b, relationship, TABLE).facts:
        if item.fact.scenario is Scenario.COUPLE_SHARED_AR:
            by_gene[item.fact.gene] = by_gene.get(item.fact.gene, Fraction(0)) + (
                item.fact.value or 0
            )
    assert all(total == 1 for total in by_gene.values())


@given(
    st.fractions(min_value=0, max_value=1),
    st.fractions(min_value=0, max_value=1),
)
def test_child_outcomes_always_sum_to_one(from_a: Fraction, from_b: Fraction) -> None:
    assert sum(rules.child_outcomes(from_a, from_b)) == 1
    assert all(0 <= outcome <= 1 for outcome in rules.child_outcomes(from_a, from_b))


@given(records_strategy, records_strategy, relationships_strategy, st.sampled_from(list(Reveal)))
def test_a_partners_private_genes_never_appear(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship, reveal: Reveal
) -> None:
    """V2.4.9. A person may only ever see genes they themselves hold."""
    assessment = couple_assessment(a, b, relationship, TABLE)
    a_genes = {f.gene for f in a.findings}
    b_genes = {f.gene for f in b.findings}
    for viewer, own, other in ((Viewer.A, a_genes, b_genes), (Viewer.B, b_genes, a_genes)):
        for fact in partner_view(assessment, viewer, reveal):
            text = f"{fact.gene} {fact.id}"
            for private in other - own:
                assert private not in text


@given(records_strategy, records_strategy, relationships_strategy)
def test_yes_no_never_names_any_gene(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship
) -> None:
    assessment = couple_assessment(a, b, relationship, TABLE)
    for viewer in Viewer:
        for fact in partner_view(assessment, viewer, Reveal.YES_NO):
            assert fact.gene is None
            assert not any(name in fact.id for name in GENES)


# --- Dominant inheritance ------------------------------------------------------------------
# One changed copy is enough, so nobody is a carrier and the person may be affected themselves.


def test_a_dominant_change_is_never_called_carrier_and_goes_to_a_person() -> None:
    """The word "carrier" would be wrong here, and the finding matters for their own health."""
    facts = person_facts([finding("LDLR")], Sex.FEMALE, TABLE)
    labels = {fact.label for fact in facts}
    assert Label.CARRIER not in labels
    assert Label.POSSIBLE_AFFECTED in labels
    assert any(Flag.POSSIBLE_AFFECTED in fact.flags for fact in facts)


def test_one_dominant_copy_passes_to_half_of_pregnancies() -> None:
    """Aa x aa: half inherit the changed copy, half inherit neither."""
    facts = person_facts([finding("LDLR")], Sex.FEMALE, TABLE)
    assert values(facts, "LDLR") == {
        Label.POSSIBLE_AFFECTED: None,
        Label.INHERITS_CHANGE: rules.ONE_HALF,
        Label.DOES_NOT_INHERIT: rules.ONE_HALF,
    }


def test_two_dominant_copies_pass_to_every_pregnancy_and_leave_no_second_group() -> None:
    facts = person_facts([finding("LDLR", zyg=HOM)], Sex.FEMALE, TABLE)
    assert values(facts, "LDLR") == {
        Label.POSSIBLE_AFFECTED: None,
        Label.INHERITS_CHANGE: rules.ONE,
    }


def test_an_x_linked_dominant_mother_splits_sons_and_daughters_alike() -> None:
    facts = person_facts([finding("PHEX")], Sex.FEMALE, TABLE)
    assert values(facts, "PHEX") == {
        Label.POSSIBLE_AFFECTED: None,
        Label.SON_INHERITS: rules.ONE_HALF,
        Label.DAUGHTER_INHERITS: rules.ONE_HALF,
    }


def test_an_x_linked_dominant_father_passes_to_every_daughter_and_no_son() -> None:
    """He has one X and gives it to each daughter; his sons get his Y. The pattern's whole point."""
    facts = person_facts([finding("PHEX", zyg=HEMI)], Sex.MALE, TABLE)
    assert values(facts, "PHEX") == {
        Label.POSSIBLE_AFFECTED: None,
        Label.SON_INHERITS: rules.ZERO,
        Label.DAUGHTER_INHERITS: rules.ONE,
    }


def test_a_dominant_finding_is_never_a_shared_recessive_result() -> None:
    """The chance comes from the parent who has it, so there is nothing to combine."""
    assessment = couple_assessment(
        record(finding("LDLR")), record(sex=Sex.MALE), Relationship.UNRELATED, TABLE
    )
    assert assessment.shared_genes == frozenset()
    assert not assessment.review_needed
    labels = {fact.fact.label for fact in assessment.facts}
    assert Label.TWO_COPIES not in labels
    assert Label.INHERITS_CHANGE in labels
    # It is the holder's own fact, so the partner is never shown it.
    for item in assessment.facts:
        if item.fact.gene == "LDLR":
            assert item.visible_to == frozenset({Viewer.A})


def test_both_partners_with_the_same_dominant_change_go_to_a_counsellor() -> None:
    assessment = couple_assessment(
        record(finding("LDLR")),
        record(finding("LDLR"), sex=Sex.MALE),
        Relationship.UNRELATED,
        TABLE,
    )
    assert assessment.review_needed
    assert assessment.shared_genes == frozenset()
    assert Label.REVIEW in {fact.fact.label for fact in assessment.facts}


def test_a_dominant_vus_still_gives_no_number() -> None:
    facts = person_facts([finding("LDLR", cls=VUS)], Sex.FEMALE, TABLE)
    assert values(facts, "LDLR") == {Label.UNCERTAIN: None}
