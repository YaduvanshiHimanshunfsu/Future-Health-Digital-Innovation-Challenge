"""Equity: the same measure, compared across groups of people, one dimension at a time.

Two faults in the original spec are avoided here (H11):
- It overwrote rows while grouping, so the last group won and real gaps vanished (it reported 2.0
  where the spread was 30 points). Here each group is aggregated first, then groups are compared.
- It published every cell. Here a group under MIN_CELL people is withheld (M9), and so is a second
  group whenever one alone is withheld, so the hidden one can't be worked out by subtracting the
  others from a total (V5.4.4).

Gaps are in percentage points between the best and worst published groups. An alert fires at the
thresholds the plan sets: 5 points between languages, 10 between reading levels (V5.4.9).
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

MIN_CELL = 10
ALERT_PP = {"lang": 5.0, "literacy": 10.0}
DEFAULT_ALERT_PP = 10.0


@dataclass(frozen=True, slots=True)
class Group:
    group: str
    # None when withheld: fewer than MIN_CELL people, or hidden to protect a group that is.
    n: int | None
    rate: float | None


@dataclass(frozen=True, slots=True)
class Gap:
    dimension: str
    groups: list[Group]
    gap_pp: float | None
    threshold_pp: float
    alert: bool


def suppress_counts(counts: Mapping[str, int]) -> set[str]:
    """Which groups to withhold: every small one, plus the next smallest if only one is small."""
    hidden = {group for group, n in counts.items() if 0 < n < MIN_CELL}
    shown = sorted((n, group) for group, n in counts.items() if group not in hidden and n > 0)
    if len(hidden) == 1 and shown:
        hidden.add(shown[0][1])
    return hidden


def gap(dimension: str, rows: Iterable[tuple[str | None, bool]]) -> Gap:
    """`rows` holds one (group, outcome) pair per person. People with no group recorded are left out
    of the comparison, never put into a group they don't belong to."""
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for group, outcome in rows:
        if group is None:
            continue
        tally[group][0] += 1
        tally[group][1] += int(outcome)
    hidden = suppress_counts({group: n for group, (n, _) in tally.items()})
    groups = [
        Group(group, None, None) if group in hidden else Group(group, n, round(100 * hits / n, 1))
        for group, (n, hits) in sorted(tally.items())
    ]
    rates = [g.rate for g in groups if g.rate is not None]
    spread = round(max(rates) - min(rates), 1) if len(rates) >= 2 else None
    threshold = ALERT_PP.get(dimension, DEFAULT_ALERT_PP)
    return Gap(dimension, groups, spread, threshold, spread is not None and spread >= threshold)


def suppress_table(cells: Mapping[tuple[str, str], int]) -> dict[tuple[str, str], int | None]:
    """A two-way table of counts with small cells withheld, then more cells withheld until no row or
    column has exactly one hidden cell, since a lone hidden cell could be recovered from the totals."""
    hidden = {key for key, n in cells.items() if 0 < n < MIN_CELL}
    rows = {r for r, _ in cells}
    columns = {c for _, c in cells}
    changed = True
    while changed:
        changed = False
        for line in [*[("row", r) for r in rows], *[("col", c) for c in columns]]:
            keys = [k for k in cells if (k[0] if line[0] == "row" else k[1]) == line[1]]
            lone = [k for k in keys if k in hidden]
            others = sorted((cells[k], k) for k in keys if k not in hidden and cells[k] > 0)
            if len(lone) == 1 and others:
                hidden.add(others[0][1])
                changed = True
    return {key: (None if key in hidden else n) for key, n in cells.items()}
