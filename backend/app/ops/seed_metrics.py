"""Synthetic programme activity, so the dashboard has numbers to show. Run inside the API container:

    docker compose exec api python -m app.ops.seed_metrics           # add, or top up
    docker compose exec api python -m app.ops.seed_metrics --remove  # take it all out again

Everything here is invented and labelled so: the dashboard says "synthetic data" (V5.4.7).
- People get fixed IDs derived from a namespace, so a second run adds nothing and --remove finds
  every row it made. They have no account, no national ID and no genetic findings.
- Journeys follow simple made-up odds through the real state machine's steps, backdated over the
  last 90 days. Comprehension scores are random around a made-up mean.
- No group is given worse odds on purpose. Any gap the dashboard shows from this data is noise, not
  a finding, and must never be presented as one.
"""

import argparse
import asyncio
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.analytics.events import emit
from app.core.config import decode_key, get_settings
from app.country_packs.loader import load_registry
from app.db.session import build_engine, build_session_factory
from app.models.analytics import Event
from app.models.case import CareCase, PathwayStep
from app.models.enums import CaseState as S
from app.models.person import Person
from app.privacy.crypto import FieldCipher
from app.privacy.kms import build_kek
from app.triage.service import reasons_aad, sla_hours

NAMESPACE = uuid.UUID("5a3c1d2e-0000-4000-8000-73796e746869")  # "synthi" in the last bytes
PEOPLE = 360
ACTOR = "system:synthetic"
LANGUAGES = ["en", "ar"]
LEVELS = ["simple", "standard", "detailed"]
PRIORITIES = [("P1", 0.05), ("P2", 0.2), ("P3", 0.35), ("P4", 0.4)]


def person_id(index: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"person-{index}")


def journey(rng: random.Random, priority: str) -> list[S]:
    """A made-up path through the real states, with made-up odds at each fork."""
    path = [S.RESULT_RELEASED]
    if priority in ("P1", "P2"):
        path.append(S.COUNSELLING_REQUESTED)
    else:
        if rng.random() < 0.85:
            path.append(S.EDUCATION_VIEWED)
            if rng.random() < 0.75:
                path.append(S.COMPREHENSION_CHECKED)
        if rng.random() < 0.08:
            return [*path, S.DECLINED_BY_USER]
        if rng.random() < (0.55 if priority == "P3" else 0.3):
            path.append(S.COUNSELLING_REQUESTED)
        else:
            return path
    if rng.random() < 0.85:
        path += [S.COUNSELLING_BOOKED]
        if rng.random() < 0.9:
            path += [S.COUNSELLING_DONE]
            if priority in ("P1", "P2") and rng.random() < 0.7:
                path += [S.CONFIRMATORY_TEST_ORDERED]
    return path


async def seed(remove: bool) -> int:
    settings = get_settings()
    if settings.is_production:
        sys.stderr.write("Synthetic activity is never added to a production database.\n")
        return 1
    engine = build_engine(settings.database_url.get_secret_value())
    factory = build_session_factory(engine)
    packs = load_registry(
        settings.packs_dir, settings.enabled_packs, settings.default_pack, production=False
    )
    pack = packs.default
    cipher = FieldCipher(build_kek(settings))
    key = decode_key(settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY")
    ids = [person_id(index) for index in range(PEOPLE)]
    try:
        async with factory() as db:
            if remove:
                cases = (
                    await db.scalars(select(CareCase.id).where(CareCase.subject_id.in_(ids)))
                ).all()
                await db.execute(delete(PathwayStep).where(PathwayStep.case_id.in_(cases)))
                await db.execute(delete(CareCase).where(CareCase.id.in_(cases)))
                await db.execute(
                    delete(Event).where(Event.subject.in_([_subject(key, i) for i in ids]))
                )
                await db.execute(delete(Person).where(Person.id.in_(ids)))
                await db.commit()
                sys.stdout.write(f"Removed the synthetic activity for {PEOPLE} people.\n")
                return 0
            existing = set((await db.scalars(select(Person.id).where(Person.id.in_(ids)))).all())
            # Demo numbers, not secrets: a seeded generator makes every run produce the same data.
            rng = random.Random(20261120)  # noqa: S311  # nosec B311
            now = datetime.now(UTC)
            added = 0
            for pid in ids:
                # Draw every number for every person, so the output doesn't depend on what exists.
                lang, level = rng.choice(LANGUAGES), rng.choice(LEVELS)
                region = rng.choice(pack.strata.regions)
                age, gender = rng.choice(pack.strata.age_bands), rng.choice(pack.strata.genders)
                priority = rng.choices([p for p, _ in PRIORITIES], [w for _, w in PRIORITIES])[0]
                path = journey(rng, priority)
                start = now - timedelta(days=rng.uniform(5, 90))
                gaps = [rng.uniform(0.2, 1.2) * sla_hours(pack, priority) for _ in path]
                pre, post = rng.betavariate(4, 4), rng.betavariate(7, 3)
                if pid in existing:
                    continue
                person = Person(
                    id=pid,
                    # Marks the row as synthetic. No account can have it: real ones are UUIDs.
                    keycloak_sub=f"synthetic:{pid}",
                    pack_code=pack.code,
                    preferred_lang=lang,
                    literacy_level=level,
                    region=region,
                    age_band=age,
                    gender=gender,
                    service_consent_at=start,
                )
                db.add(person)
                # No relationship is mapped, so the person must exist before their case.
                await db.flush()
                case = CareCase(
                    subject_id=pid,
                    priority=priority,
                    reasons_enc=b"",
                    state=path[-1].value,
                    step_due=now + timedelta(hours=sla_hours(pack, priority)),
                    created_at=start,
                )
                db.add(case)
                await db.flush()
                case.reasons_enc = await cipher.encrypt_json(["synthetic"], aad=reasons_aad(case))
                at, previous = start, None
                for state, wait in zip(path, gaps, strict=True):
                    db.add(
                        PathwayStep(
                            case_id=case.id,
                            from_state=previous,
                            to_state=state.value,
                            actor=ACTOR,
                            at=at,
                        )
                    )
                    previous, at = state.value, at + timedelta(hours=wait)
                if S.EDUCATION_VIEWED in path:
                    emit(
                        db,
                        key,
                        "comprehension_pre",
                        person,
                        value=round(pre, 2),
                        at=start + timedelta(hours=1),
                    )
                    if S.COMPREHENSION_CHECKED in path or rng.random() < 0.5:
                        emit(
                            db,
                            key,
                            "comprehension_post",
                            person,
                            value=round(post, 2),
                            at=start + timedelta(hours=2),
                        )
                added += 1
            await db.commit()
            sys.stdout.write(
                f"Added synthetic activity for {added} people ({PEOPLE - added} already there).\n"
            )
            return 0
    finally:
        await engine.dispose()


def _subject(key: bytes, pid: uuid.UUID) -> str:
    from app.analytics.events import pseudonym

    return pseudonym(key, pid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", action="store_true")
    sys.exit(asyncio.run(seed(parser.parse_args().remove)))
