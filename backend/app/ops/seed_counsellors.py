"""A fictional counselling team for each country, with a week of times. Run inside the API container:

    docker compose exec api python -m app.ops.seed_counsellors           # add, or top up
    docker compose exec api python -m app.ops.seed_counsellors --remove  # cancel their open times

Everything here is invented and labelled so: each profile is marked fictional, and screens say so
beside the name. The people have no account and can't sign in.

- Times run from now to a week ahead, in each country's working hours. About a third are already
  taken by other (unnamed, non-existent) clients, so the calendar looks like a real one.
- One counsellor per country is given a session covering the moment this runs, so "in a session"
  can be seen in a demo. It is computed from that calendar entry like any other status.
- Safe to repeat: a time that already exists is left alone, and nothing anyone booked is touched.
  The API's database role can't delete appointments, so nothing here tries to.
"""

import argparse
import asyncio
import hashlib
import random
import sys
import uuid
from datetime import UTC, datetime, time, timedelta, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory
from app.models.appointment import Appointment
from app.models.counsellor import CounsellorProfile
from app.models.enums import AppointmentMode, AppointmentStatus, CounsellorRole
from app.models.person import Person

NAMESPACE = uuid.UUID("5a3c1d2e-0000-4000-8000-636f756e7365")  # "counse" in the last bytes
DAYS_AHEAD = 7
# Local starting times. Neither country moves its clocks, so a fixed offset is exact.
HOURS = [time(9), time(10), time(11, 30), time(13, 30), time(14, 30), time(16)]
TAKEN_SHARE = 0.35

R = CounsellorRole
# Invented names. Country code: (UTC offset, days off as weekday numbers, the team).
TEAMS: dict[str, tuple[timezone, set[int], list[tuple[str, CounsellorRole, list[str]]]]] = {
    "ae-abu-dhabi": (
        timezone(timedelta(hours=4)),
        {5, 6},
        [
            ("Noura Al Ameri", R.GENETIC_COUNSELLOR, ["ar", "en"]),
            ("Sameer Haddad", R.CLINICAL_GENETICIST, ["ar", "en"]),
            ("Grace Mathew", R.COUNSELLING_NURSE, ["en"]),
        ],
    ),
}


def counsellor_id(pack: str, index: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"counsellor-{pack}-{index}")


def _draw(*parts: object) -> random.Random:
    # Demo choices, not secrets: each time gets its own seeded generator, so a repeat run makes the
    # same decision for a time it has already seen, whatever else has changed.
    seed = int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "big")
    return random.Random(seed)  # noqa: S311  # nosec B311


async def _overlaps(db: AsyncSession, who: uuid.UUID, start: datetime, end: datetime) -> bool:
    found = await db.scalar(
        select(Appointment.id).where(
            Appointment.counsellor_id == who,
            Appointment.status != AppointmentStatus.CANCELLED.value,
            and_(Appointment.starts_at < end, Appointment.ends_at > start),
        )
    )
    return found is not None


async def _member(
    db: AsyncSession, pack: str, index: int, entry: tuple[str, R, list[str]]
) -> uuid.UUID:
    name, role, languages = entry
    pid = counsellor_id(pack, index)
    if await db.get(Person, pid) is None:
        db.add(
            Person(
                id=pid,
                # Marks the row as synthetic. No account can have it: real ones are UUIDs.
                keycloak_sub=f"synthetic:{pid}",
                pack_code=pack,
                preferred_lang=languages[0],
            )
        )
        await db.flush()
    profile = await db.get(CounsellorProfile, pid)
    if profile is None:
        db.add(
            CounsellorProfile(
                person_id=pid,
                display_name=name,
                role=role.value,
                languages=languages,
                fictional=True,
            )
        )
    else:
        profile.display_name, profile.role, profile.languages = name, role.value, languages
    return pid


async def _week(
    db: AsyncSession,
    pid: uuid.UUID,
    zone: timezone,
    days_off: set[int],
    role: R,
    lang: str,
    now: datetime,
) -> int:
    minutes = 45 if role is R.CLINICAL_GENETICIST else 30
    added = 0
    today = now.astimezone(zone).date()
    for offset in range(DAYS_AHEAD + 1):
        day = today + timedelta(days=offset)
        if day.weekday() in days_off:
            continue
        for start_local in HOURS:
            start = datetime.combine(day, start_local, tzinfo=zone).astimezone(UTC)
            if start <= now + timedelta(minutes=5):
                continue
            end = start + timedelta(minutes=minutes)
            if await _overlaps(db, pid, start, end):
                continue
            draw = _draw(pid, start.isoformat())
            taken = draw.random() < TAKEN_SHARE
            mode = draw.choice([AppointmentMode.VIDEO, AppointmentMode.IN_PERSON])
            db.add(
                Appointment(
                    counsellor_id=pid,
                    starts_at=start,
                    ends_at=end,
                    mode=mode.value,
                    lang=lang,
                    # Taken by another client: no case, so it points at nobody.
                    status=(AppointmentStatus.BOOKED if taken else AppointmentStatus.OPEN).value,
                )
            )
            added += 1
    return added


async def _session_now(db: AsyncSession, pid: uuid.UUID, lang: str, now: datetime) -> None:
    """Gives this counsellor a session covering the present moment, unless they already have one."""
    covering = (
        await db.scalars(
            select(Appointment).where(
                Appointment.counsellor_id == pid,
                Appointment.status != AppointmentStatus.CANCELLED.value,
                Appointment.starts_at <= now,
                Appointment.ends_at > now,
            )
        )
    ).first()
    if covering is not None:
        if covering.status == AppointmentStatus.OPEN.value and covering.case_id is None:
            covering.status = AppointmentStatus.BOOKED.value
        return
    start = now.replace(second=0, microsecond=0) - timedelta(minutes=15)
    end = start + timedelta(minutes=45)
    if await _overlaps(db, pid, start, end):
        return
    db.add(
        Appointment(
            counsellor_id=pid,
            starts_at=start,
            ends_at=end,
            mode=AppointmentMode.IN_PERSON.value,
            lang=lang,
            status=AppointmentStatus.BOOKED.value,
        )
    )


async def seed(remove: bool) -> int:
    settings = get_settings()
    if settings.is_production:
        sys.stderr.write("A fictional team is never added to a production database.\n")
        return 1
    engine = build_engine(settings.database_url.get_secret_value())
    factory = build_session_factory(engine)
    now = datetime.now(UTC)
    packs = [code for code in settings.enabled_packs if code in TEAMS]
    try:
        async with factory() as db:
            if remove:
                ids = [counsellor_id(p, i) for p in packs for i in range(len(TEAMS[p][2]))]
                done = await db.execute(
                    update(Appointment)
                    .where(
                        Appointment.counsellor_id.in_(ids),
                        Appointment.case_id.is_(None),
                        Appointment.starts_at > now,
                    )
                    .values(status=AppointmentStatus.CANCELLED.value)
                    .execution_options(synchronize_session=False)
                )
                await db.commit()
                cancelled = done.rowcount  # type: ignore[attr-defined]
                sys.stdout.write(f"Cancelled {cancelled} future times. Bookings were left alone.\n")
                return 0
            added = 0
            for pack in packs:
                zone, days_off, members = TEAMS[pack]
                for index, entry in enumerate(members):
                    pid = await _member(db, pack, index, entry)
                    added += await _week(db, pid, zone, days_off, entry[1], entry[2][0], now)
                    if index == 1:
                        await _session_now(db, pid, entry[2][0], now)
            await db.commit()
    finally:
        await engine.dispose()
    sys.stdout.write(
        f"Fictional counselling teams ready in {len(packs)} countries ({added} new times).\n"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--remove", action="store_true", help="cancel the team's open future times")
    return asyncio.run(seed(parser.parse_args().remove))


if __name__ == "__main__":
    raise SystemExit(main())
