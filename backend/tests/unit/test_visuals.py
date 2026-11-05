from dataclasses import replace
from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from app.risk_engine.engine import _fact, person_facts
from app.risk_engine.frequencies import GeneInfo, GeneTable
from app.risk_engine.types import (
    Classification,
    Finding,
    Inheritance,
    Label,
    Scenario,
    Sex,
    Zygosity,
)
from app.risk_engine.visuals import icon_array, punnett, split_counts, visuals_for

TABLE = GeneTable(
    {
        "HBB": GeneInfo("HBB", Inheritance.AUTOSOMAL_RECESSIVE, Fraction(1, 20), Fraction(49, 50)),
        "DMD": GeneInfo("DMD", Inheritance.X_LINKED, Fraction(1, 2000), Fraction(9, 10)),
    }
)


def shared(two: Fraction, carrier: Fraction, neither: Fraction) -> list:
    return [
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, two, "c"),
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.CARRIER, carrier, "c"),
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.NEITHER, neither, "c"),
    ]


def test_icon_counts_match_the_facts() -> None:
    """V2.5.2."""
    array = icon_array(
        {"two_copies": Fraction(1, 4), "carrier": Fraction(1, 2), "neither": Fraction(1, 4)}, 100
    )
    assert array["total"] == 100
    assert {g["key"]: g["count"] for g in array["groups"]} == {
        "two_copies": 25,
        "carrier": 50,
        "neither": 25,
    }


@given(
    st.lists(st.integers(min_value=1, max_value=997), min_size=2, max_size=5),
    st.sampled_from([100, 1000]),
)
def test_icon_counts_always_add_up_to_the_total(weights: list[int], total: int) -> None:
    whole = sum(weights)
    outcomes = {f"g{i}": Fraction(weight, whole) for i, weight in enumerate(weights)}
    counts = split_counts(outcomes, total)
    assert sum(counts.values()) == total
    assert all(abs(counts[key] - outcomes[key] * total) <= 1 for key in outcomes)


def test_single_carrier_gets_no_square() -> None:
    """V2.5.3. The original spec drew a 25% square for someone with no partner in the picture."""
    facts = person_facts(
        [Finding("HBB", Classification.PATHOGENIC, Zygosity.HETEROZYGOUS)], Sex.FEMALE, TABLE
    )
    assert visuals_for(facts) == []


def test_x_linked_uses_its_own_diagram_and_never_a_punnett_square() -> None:
    facts = person_facts(
        [Finding("DMD", Classification.PATHOGENIC, Zygosity.HETEROZYGOUS)], Sex.FEMALE, TABLE
    )
    visuals = visuals_for(facts)
    assert [visual["type"] for visual in visuals] == ["x_linked"]
    assert {child["key"]: child["percent"] for child in visuals[0]["children"]} == {
        "son_affected": "50",
        "daughter_carrier": "50",
    }


def test_uncertain_finding_gets_no_visual_at_all() -> None:
    facts = person_facts(
        [Finding("HBB", Classification.UNCERTAIN, Zygosity.HETEROZYGOUS)], Sex.FEMALE, TABLE
    )
    assert visuals_for(facts) == []


def test_shared_finding_gets_an_icon_array_and_a_square() -> None:
    visuals = visuals_for(shared(Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)))
    assert [visual["type"] for visual in visuals] == ["icon_array", "punnett"]


def test_square_follows_the_parents_genotypes() -> None:
    assert punnett(Fraction(1, 4))["cells"] == [["AA", "Aa"], ["aA", "aa"]]
    assert punnett(Fraction(1, 2))["cells"] == [["aA", "aa"], ["aA", "aa"]]
    assert punnett(Fraction(1))["cells"] == [["aa", "aa"], ["aa", "aa"]]
    assert punnett(Fraction(1, 3)) is None


def test_square_legend_uses_the_careful_wording() -> None:
    legend = punnett(Fraction(1, 4))["legend"]
    assert legend["aa"] == "two_copies"
    assert "affected" not in legend.values()


def test_share_of_unusual_chance_has_no_square_but_keeps_the_icons() -> None:
    visuals = visuals_for(shared(Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)))
    assert [visual["type"] for visual in visuals] == ["icon_array"]


def test_small_residual_uses_the_larger_grid() -> None:
    fact = _fact(
        Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE, "HBB", Label.TWO_COPIES, Fraction(1, 400), "c"
    )
    visual = visuals_for([fact])[0]
    assert visual["total"] == 1000
    assert sum(group["count"] for group in visual["groups"]) == 1000


def test_larger_residual_uses_the_smaller_grid() -> None:
    fact = _fact(
        Scenario.COUPLE_ONE_CARRIER_UNTESTED, "HBB", Label.TWO_COPIES, Fraction(1, 40), "c"
    )
    assert visuals_for([fact])[0]["total"] == 100


def test_tiny_residual_stays_as_words() -> None:
    fact = _fact(
        Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE, "HBB", Label.TWO_COPIES, Fraction(1, 3804), "c"
    )
    assert visuals_for([fact]) == []


def test_with_gene_names_hidden_each_shared_gene_keeps_its_own_picture() -> None:
    """Grouping by name alone would have merged them, silently hiding the second gene."""
    facts = [
        replace(fact, gene=None, id=f"couple_shared_ar:shared-{number}:{fact.label.value}")
        for number, chance in ((1, Fraction(1, 4)), (2, Fraction(1, 2)))
        for fact in shared(chance, Fraction(1, 2), Fraction(1, 2) - chance + Fraction(0))
    ]
    arrays = [visual for visual in visuals_for(facts) if visual["type"] == "icon_array"]
    assert len(arrays) == 2
    assert all(visual["gene"] is None for visual in arrays)
