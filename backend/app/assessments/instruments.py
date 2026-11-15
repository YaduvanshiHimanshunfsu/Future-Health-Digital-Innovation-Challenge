"""Questions for checking understanding, and for noticing when a decision feels unsupported.

Teach-back tests the explanation, not the person (5.3 goal): if most people miss an item, the
explanation is what changes. Getting one wrong is never a mark against anyone, and failing twice
offers a counsellor, never a verdict.

Honest labels (O5.3.2, V5.3.4):
- Teach-back items are the team's own, a draft awaiting counsellor and native-speaker review.
- SURE is the published four-item decisional-conflict screen (Legare et al., 2010), used here in
  the team's adapted wording. It is NOT validated in Arabic. Its authors make it available
  for use with citation; that permission still has to be confirmed in writing before any real use.
- MMIC and GCOS are named in the plan but not offered: no adapted version exists yet, and showing
  an unvalidated stand-in under their names would overclaim.

Arabic has no items, because Arabic text waits on approval. Arabic pages get English, and say so.
"""

from dataclasses import dataclass

from app.models.enums import Instrument

PASS_MARK = 0.8


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    text: dict[str, str]
    options: dict[str, list[str]]
    # The index of the right option. None for items with no right answer, such as SURE's.
    correct: int | None


@dataclass(frozen=True, slots=True)
class InstrumentDef:
    key: Instrument
    status: str
    citation: str
    items: tuple[Item, ...]


TEACH_BACK = InstrumentDef(
    key=Instrument.TEACH_BACK,
    status="draft: team-written, awaiting counsellor and native-speaker review",
    citation="Samvid team",
    items=(
        Item(
            "tb1",
            {
                "en": "Being a carrier usually means...",
            },
            {
                "en": [
                    "You have the condition",
                    "You carry one changed copy, which usually doesn't cause illness",
                    "Your children will have the condition",
                ],
            },
            1,
        ),
        Item(
            "tb2",
            {
                "en": "Can a carrier pass the change on to a child?",
            },
            {
                "en": ["Yes, a child may inherit one copy", "No, never", "Only to sons"],
            },
            0,
        ),
        Item(
            "tb3",
            {
                "en": "Does an earlier pregnancy change the chance for the next one?",
            },
            {
                "en": [
                    "Yes, the chance goes down after an affected child",
                    "No, each pregnancy has the same chance",
                    "Yes, the chance goes up each time",
                ],
            },
            1,
        ),
        Item(
            "tb4",
            {
                "en": "If a screening test finds nothing shared, is there any chance left?",
            },
            {
                "en": [
                    "The test was wrong",
                    "No chance at all",
                    "Some chance remains, because no test finds every change",
                ],
            },
            2,
        ),
        Item(
            "tb5",
            {
                "en": "Who decides what to do with this information?",
            },
            {
                "en": ["You, with support if you want it", "The app", "Your family"],
            },
            0,
        ),
    ),
)

SURE = InstrumentDef(
    key=Instrument.SURE,
    status="adapted, not validated in Arabic",
    citation="Legare F, et al. Can Fam Physician 2010;56(8):e308-14 (the SURE test)",
    items=tuple(
        Item(key, text, {"en": ["Yes", "No"]}, None)
        for key, text in (
            (
                "s1",
                {
                    "en": "Do you feel sure about what is right for you?",
                },
            ),
            (
                "s2",
                {
                    "en": "Do you know the benefits and risks of each option?",
                },
            ),
            (
                "s3",
                {
                    "en": "Are you clear about which benefits and risks matter most to you?",
                },
            ),
            (
                "s4",
                {
                    "en": "Do you have enough support to make a choice?",
                },
            ),
        )
    ),
)

OFFERED: dict[Instrument, InstrumentDef] = {
    Instrument.TEACH_BACK: TEACH_BACK,
    Instrument.SURE: SURE,
}


# The questions exist in English only for now. Any other language gets English, and the screen says so.
WRITTEN_IN = ("en",)


def language_for(language: str) -> str:
    return language if language in WRITTEN_IN else "en"
