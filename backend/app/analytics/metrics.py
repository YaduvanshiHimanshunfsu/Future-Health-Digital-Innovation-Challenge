"""Programme metrics, each from a named source, so any number on the dashboard traces to rows.

| Measure | Source |
|---|---|
| Funnel, time to counselling, time to referral, uptake | `pathway_step`, whose rows every state change writes |
| Comprehension | `event` rows `comprehension_pre` and `comprehension_post`, paired by pseudonym |
| AI answers and blocked drafts | `message` rows from the assistant: source and validator flags |
| Privacy | `audit_log` rows for revocations (with their latency) and denied access |
| Groups | the person's own reporting groups (language, reading level, region, age band, gender) |

Time is measured from RESULT_RELEASED, the first step of every case, so escalated cases count too
(V5.4.2): in the original spec they skipped the state machine and fell out of the metric.

Nothing here counts marriages, or treats any reproductive choice as success (V5.4.8). Uptake means
someone reached counselling, which is offered to all and declined freely.
"""

import statistics
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.fairness import MIN_CELL, gap, suppress_table
from app.country_packs.loader import CountryPack
from app.models.analytics import Event
from app.models.audit import AuditLog
from app.models.case import CareCase, PathwayStep
from app.models.conversation import Message
from app.models.enums import CaseState as S
from app.models.person import Person
from app.schemas.analytics import (
    AiOut,
    AnalyticsOut,
    ComprehensionOut,
    CountOut,
    DurationOut,
    EquityOut,
    GroupOut,
    HeatCellOut,
    PrivacyOut,
)
from app.triage.service import sla_hours

FUNNEL = [
    S.RESULT_RELEASED,
    S.EDUCATION_VIEWED,
    S.COMPREHENSION_CHECKED,
    S.COUNSELLING_REQUESTED,
    S.COUNSELLING_BOOKED,
    S.COUNSELLING_DONE,
    S.CONFIRMATORY_TEST_ORDERED,
    S.REPRO_GENOMICS_REFERRED,
]
REFERRED = {S.CONFIRMATORY_TEST_ORDERED.value, S.REPRO_GENOMICS_REFERRED.value}
DIMENSIONS = ["lang", "literacy", "region", "age_band", "gender"]
PASS = 0.8


def _count(n: int) -> int | None:
    return n if n >= MIN_CELL else None


def _median(hours: list[float]) -> float | None:
    return round(statistics.median(hours), 1) if len(hours) >= MIN_CELL else None


def _hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


async def _pathways(
    db: AsyncSession,
) -> tuple[
    dict[uuid.UUID, dict[str, datetime]], dict[uuid.UUID, CareCase], dict[uuid.UUID, Person]
]:
    """First time each case reached each state, with the case and its person."""
    rows = (
        await db.execute(
            select(PathwayStep.case_id, PathwayStep.to_state, PathwayStep.at).order_by(
                PathwayStep.at
            )
        )
    ).all()
    first: dict[uuid.UUID, dict[str, datetime]] = defaultdict(dict)
    for case_id, state, at in rows:
        first[case_id].setdefault(state, at)
    cases = {c.id: c for c in (await db.scalars(select(CareCase))).all()}
    people = {
        p.id: p
        for p in (
            await db.scalars(
                select(Person).where(Person.id.in_({c.subject_id for c in cases.values()}))
            )
        ).all()
    }
    return first, cases, people


def _strata(person: Person | Event | None, dimension: str) -> str | None:
    return getattr(person, dimension, None) if person is not None else None


async def overview(
    db: AsyncSession, pack: CountryPack, *, now: datetime | None = None
) -> AnalyticsOut:
    first, cases, people = await _pathways(db)
    released = {cid: seen for cid, seen in first.items() if S.RESULT_RELEASED.value in seen}

    funnel = [
        CountOut(
            key=state.value,
            value=_count(sum(1 for seen in released.values() if state.value in seen)),
        )
        for state in FUNNEL
    ]

    to_counselling: dict[str, list[float]] = defaultdict(list)
    to_referral: list[float] = []
    for cid, seen in released.items():
        start = seen[S.RESULT_RELEASED.value]
        case = cases.get(cid)
        if case is None:
            continue
        if S.COUNSELLING_BOOKED.value in seen:
            to_counselling[case.priority].append(_hours(start, seen[S.COUNSELLING_BOOKED.value]))
        reached = [at for state, at in seen.items() if state in REFERRED]
        if reached:
            to_referral.append(_hours(start, min(reached)))
    durations = [
        DurationOut(
            key=priority,
            median_hours=_median(to_counselling[priority]),
            cases=_count(len(to_counselling[priority])),
            sla_hours=sla_hours(pack, priority),
        )
        for priority in ("P1", "P2", "P3", "P4")
    ]
    referral = DurationOut(
        key="all", median_hours=_median(to_referral), cases=_count(len(to_referral)), sla_hours=None
    )

    events = (
        await db.scalars(
            select(Event)
            .where(Event.kind.in_(["comprehension_pre", "comprehension_post"]))
            .order_by(Event.at)
        )
    ).all()
    pre: dict[str, Event] = {}
    post: dict[str, Event] = {}
    for event in events:
        if event.subject is None or event.value is None:
            continue
        if event.kind == "comprehension_pre":
            pre.setdefault(event.subject, event)
        else:
            post[event.subject] = event
    paired = [(pre[s].value, post[s].value) for s in pre.keys() & post.keys()]
    enough = len(paired) >= MIN_CELL
    comprehension = ComprehensionOut(
        pairs=_count(len(paired)),
        pre_mean=round(statistics.fmean(p for p, _ in paired), 3) if enough else None,  # type: ignore[misc]
        post_mean=round(statistics.fmean(q for _, q in paired), 3) if enough else None,  # type: ignore[misc]
        change=round(statistics.fmean(q - p for p, q in paired), 3) if enough else None,  # type: ignore[operator]
    )

    answers = (
        await db.execute(
            select(Message.boundary, Message.source, Message.validator_flags).where(
                Message.role == "assistant"
            )
        )
    ).all()
    by_boundary: dict[str, int] = defaultdict(int)
    for boundary, _, _ in answers:
        by_boundary[boundary or "unknown"] += 1
    boundaries = [CountOut(key=key, value=_count(n)) for key, n in sorted(by_boundary.items())]
    ai = AiOut(
        answers=_count(len(answers)),
        model_written=_count(sum(1 for _, source, _ in answers if source == "llm")),
        template=_count(sum(1 for _, source, _ in answers if source == "template")),
        drafts_blocked=_count(sum(1 for _, _, flags in answers if flags)),
    )

    audit = (
        await db.execute(
            select(AuditLog.action, AuditLog.meta).where(
                AuditLog.action.in_(["consent.revoke", "access.denied"])
            )
        )
    ).all()
    latencies = sorted(
        float(meta["latency_ms"])
        for action, meta in audit
        if action == "consent.revoke" and "latency_ms" in (meta or {})
    )
    privacy = PrivacyOut(
        revocations=_count(sum(1 for action, _ in audit if action == "consent.revoke")),
        p95_revoke_ms=round(statistics.quantiles(latencies, n=20)[-1], 1)
        if len(latencies) >= MIN_CELL
        else None,
        denied_access=_count(sum(1 for action, _ in audit if action == "access.denied")),
    )

    equity: list[EquityOut] = []
    for dimension in DIMENSIONS:
        understood = gap(
            dimension, [(_strata(post[s], dimension), (post[s].value or 0) >= PASS) for s in post]
        )
        uptake = gap(
            dimension,
            [
                (
                    _strata(people.get(cases[cid].subject_id), dimension),
                    S.COUNSELLING_BOOKED.value in seen,
                )
                for cid, seen in released.items()
                if cid in cases
            ],
        )
        for measure, result in (
            ("comprehension_pass", understood),
            ("counselling_reached", uptake),
        ):
            equity.append(
                EquityOut(
                    measure=measure,
                    dimension=dimension,
                    groups=[GroupOut(group=g.group, n=g.n, rate=g.rate) for g in result.groups],
                    gap_pp=result.gap_pp,
                    threshold_pp=result.threshold_pp,
                    alert=result.alert,
                )
            )

    cells: dict[tuple[str, str], int] = defaultdict(int)
    for cid in released:
        person = people.get(cases[cid].subject_id) if cid in cases else None
        if person is not None and person.region and person.age_band:
            cells[(person.region, person.age_band)] += 1
    table = suppress_table(cells)
    heatmap = [HeatCellOut(row=r, column=c, value=v) for (r, c), v in sorted(table.items())]

    return AnalyticsOut(
        synthetic=True,
        generated_at=now or datetime.now(UTC),
        min_cell=MIN_CELL,
        funnel=funnel,
        time_to_counselling=durations,
        time_to_referral=referral,
        comprehension=comprehension,
        boundaries=boundaries,
        ai=ai,
        privacy=privacy,
        equity=equity,
        heatmap=heatmap,
        sources={
            "funnel": "pathway_step: first arrival of each case at each state",
            "time_to_counselling": "pathway_step: RESULT_RELEASED to COUNSELLING_BOOKED, per priority",
            "time_to_referral": "pathway_step: RESULT_RELEASED to the first referral step, all cases",
            "comprehension": "event: comprehension_pre and comprehension_post, paired by pseudonym",
            "boundaries": "message: assistant answers by boundary",
            "ai": "message: assistant answers by source and validator flags",
            "privacy": "audit_log: consent.revoke (latency_ms) and access.denied",
            "equity": "the two measures above, per reporting group of the person",
            "heatmap": "person: region by age band, for people with a released result",
        },
    )
