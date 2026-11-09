"""Programme metrics. Every count of people under the minimum cell size arrives as null."""

from datetime import datetime

from app.schemas.common import Out


class CountOut(Out):
    key: str
    value: int | None


class DurationOut(Out):
    key: str
    # Median hours, null when fewer cases than the minimum cell size.
    median_hours: float | None
    cases: int | None
    sla_hours: int | None


class GroupOut(Out):
    group: str
    n: int | None
    rate: float | None


class EquityOut(Out):
    measure: str
    dimension: str
    groups: list[GroupOut]
    gap_pp: float | None
    threshold_pp: float
    alert: bool


class ComprehensionOut(Out):
    pairs: int | None
    pre_mean: float | None
    post_mean: float | None
    change: float | None


class AiOut(Out):
    answers: int | None
    model_written: int | None
    template: int | None
    drafts_blocked: int | None


class PrivacyOut(Out):
    revocations: int | None
    p95_revoke_ms: float | None
    denied_access: int | None


class HeatCellOut(Out):
    row: str
    column: str
    value: int | None


class AnalyticsOut(Out):
    # Always true in this prototype, and shown on the dashboard (V5.4.7).
    synthetic: bool
    generated_at: datetime
    min_cell: int
    funnel: list[CountOut]
    time_to_counselling: list[DurationOut]
    time_to_referral: DurationOut
    comprehension: ComprehensionOut
    boundaries: list[CountOut]
    ai: AiOut
    privacy: PrivacyOut
    equity: list[EquityOut]
    heatmap: list[HeatCellOut]
    # Where each number comes from, so any of them can be traced back to its rows (O5.4.1).
    sources: dict[str, str]
