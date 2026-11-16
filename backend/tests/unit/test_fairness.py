"""Equity gaps and small-cell suppression. Checks V5.4.1, V5.4.3, V5.4.4 and V5.4.9."""

from hypothesis import given
from hypothesis import strategies as st

from app.analytics.fairness import MIN_CELL, gap, suppress_counts, suppress_table


def rows(group: str, n: int, hits: int) -> list[tuple[str | None, bool]]:
    return [(group, index < hits) for index in range(n)]


def test_the_real_spread_is_reported() -> None:
    """V5.4.1. 80% against 50% is a 30-point gap. The original spec reported 2.0 here."""
    result = gap("lang", [*rows("en", 20, 16), *rows("ar", 20, 10)])
    assert result.gap_pp == 30.0
    assert result.alert


def test_a_hand_worked_example_matches() -> None:
    """V5.4.3. 12 of 15 is 80.0%; 9 of 12 is 75.0%; 7 of 10 is 70.0%. Spread: 10 points."""
    result = gap(
        "literacy", [*rows("simple", 15, 12), *rows("standard", 12, 9), *rows("detailed", 10, 7)]
    )
    assert {g.group: g.rate for g in result.groups} == {
        "detailed": 70.0,
        "simple": 80.0,
        "standard": 75.0,
    }
    assert result.gap_pp == 10.0
    assert result.alert  # 10 points meets the reading-level threshold


def test_alerts_use_the_thresholds_the_plan_sets() -> None:
    """V5.4.9: 5 points between languages, 10 between reading levels."""
    four = [*rows("en", 50, 40), *rows("ar", 50, 38)]
    assert gap("lang", four).gap_pp == 4.0 and not gap("lang", four).alert
    assert gap("lang", [*rows("en", 20, 16), *rows("ar", 20, 15)]).alert
    assert not gap("literacy", [*rows("simple", 20, 16), *rows("standard", 20, 15)]).alert


def test_small_groups_are_withheld_and_cannot_be_recovered_by_subtraction() -> None:
    """V5.4.4. With one small group hidden, the next smallest is hidden too."""
    result = gap("region", [*rows("a", 40, 20), *rows("b", 12, 6), *rows("c", 3, 3)])
    shown = {g.group: g.n for g in result.groups}
    assert shown == {"a": 40, "b": None, "c": None}


def test_people_with_no_group_are_left_out_not_misfiled() -> None:
    result = gap("gender", [*rows("woman", 12, 6), (None, True), (None, True)])
    assert [g.n for g in result.groups] == [12]


def test_a_two_way_table_never_has_a_lone_hidden_cell_in_a_line() -> None:
    table = {("r1", "c1"): 30, ("r1", "c2"): 4, ("r2", "c1"): 25, ("r2", "c2"): 40}
    out = suppress_table(table)
    assert out[("r1", "c2")] is None
    hidden_by_row = {
        r: sum(1 for k, v in out.items() if k[0] == r and v is None) for r in ("r1", "r2")
    }
    hidden_by_col = {
        c: sum(1 for k, v in out.items() if k[1] == c and v is None) for c in ("c1", "c2")
    }
    assert all(count != 1 for count in [*hidden_by_row.values(), *hidden_by_col.values()])


@given(
    st.dictionaries(st.sampled_from("abcdef"), st.integers(min_value=1, max_value=60), min_size=1)
)
def test_suppression_never_leaves_one_hidden_group_alone(counts: dict[str, int]) -> None:
    hidden = suppress_counts(counts)
    assert all(counts[g] >= MIN_CELL for g in counts if g not in hidden)
    assert len(hidden) != 1 or len(counts) == 1


@given(
    st.dictionaries(
        st.tuples(st.sampled_from("xyz"), st.sampled_from("pqr")),
        st.integers(min_value=1, max_value=50),
        min_size=4,
    )
)
def test_table_suppression_holds_for_any_table(cells: dict[tuple[str, str], int]) -> None:
    out = suppress_table(cells)
    for value in out.values():
        assert value is None or value >= MIN_CELL
    for axis in (0, 1):
        for name in {k[axis] for k in cells}:
            line = [k for k in cells if k[axis] == name]
            hidden = [k for k in line if out[k] is None]
            shown = [k for k in line if out[k] is not None]
            assert len(hidden) != 1 or not shown
