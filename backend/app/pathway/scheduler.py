"""The overdue scan, run by the worker every few minutes (V5.1.6).

For each case past its step deadline:
- it's marked stalled, which puts it in front of the care team;
- if the step is waiting on the person, they get one gentle reminder for that step, unless they
  declined care or opted out of reminders (V5.1.4). The text names nothing (`notifications`);
- if it's still waiting on them two full windows later, it's recorded as lost to follow-up
  (O5.1.3), so it counts in the metrics instead of quietly ageing. They can come back any time.

Each case is handled in its own transaction. A case someone changed mid-scan is skipped, not
overwritten, and the next scan sees it fresh.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from app.analytics.events import emit, pseudonym
from app.country_packs.loader import PackRegistry
from app.models.case import CareCase
from app.models.enums import CaseState as S
from app.models.person import Person
from app.notifications.service import Notifier
from app.pathway.service import RESTING, advance
from app.triage.service import sla_hours

log = logging.getLogger(__name__)

ACTOR = "system:scheduler"
# Steps where the next move is the person's. Steps waiting on the care team never remind them.
WAITING_ON_PERSON = frozenset({S.RESULT_RELEASED, S.EDUCATION_VIEWED, S.COMPREHENSION_CHECKED})
LOST_AFTER_WINDOWS = 2


@dataclass
class ScanResult:
    stalled: list[str] = field(default_factory=list)
    reminded: list[str] = field(default_factory=list)
    lost: list[str] = field(default_factory=list)


async def scan(
    factory: async_sessionmaker[AsyncSession],
    packs: PackRegistry,
    notifier: Notifier,
    analytics_key: bytes,
    *,
    now: datetime | None = None,
) -> ScanResult:
    moment = now or datetime.now(UTC)
    result = ScanResult()
    async with factory() as db:
        due = (
            await db.scalars(
                select(CareCase.id).where(
                    CareCase.state.not_in([s.value for s in RESTING]), CareCase.step_due < moment
                )
            )
        ).all()
    for case_id in due:
        async with factory() as db:
            try:
                await _one(db, case_id, packs, notifier, analytics_key, moment, result)
                await db.commit()
            except StaleDataError:
                await db.rollback()
                log.info("scan_skipped_changed_case")
    log.info(
        "pathway_scan",
        extra={
            "ctx": {
                "stalled": len(result.stalled),
                "reminded": len(result.reminded),
                "lost": len(result.lost),
            }
        },
    )
    return result


async def _one(
    db: AsyncSession,
    case_id: object,
    packs: PackRegistry,
    notifier: Notifier,
    key: bytes,
    moment: datetime,
    result: ScanResult,
) -> None:
    case = await db.get(CareCase, case_id)
    if case is None or S(case.state) in RESTING or case.step_due >= moment:
        return
    person = await db.get(Person, case.subject_id)
    pack = (packs.get(person.pack_code) if person else None) or packs.default
    window = timedelta(hours=sla_hours(pack, case.priority))
    waiting = S(case.state) in WAITING_ON_PERSON

    if waiting and case.step_due + LOST_AFTER_WINDOWS * window < moment:
        await advance(db, case, S.LOST_TO_FOLLOW_UP, actor=ACTOR, pack=pack, now=moment)
        result.lost.append(str(case.id))
        return

    if not case.stalled:
        case.stalled = True
        emit(db, key, "case_stalled", person, at=moment)
        result.stalled.append(str(case.id))

    if waiting and person is not None and case.reminded_at is None and not person.reminders_opt_out:
        await notifier.send(pseudonym(key, person.id), "reminder", person.preferred_lang)
        case.reminded_at = moment
        emit(db, key, "reminder_sent", person, at=moment)
        result.reminded.append(str(case.id))
