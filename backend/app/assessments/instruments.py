"""Questions for checking understanding, and for noticing when a decision feels unsupported.

Teach-back tests the explanation, not the person (5.3 goal): if most people miss an item, the
explanation is what changes. Getting one wrong is never a mark against anyone, and failing twice
offers a counsellor, never a verdict.

Honest labels (O5.3.2, V5.3.4):
- Teach-back items are the team's own, a draft awaiting counsellor and native-speaker review.
- SURE is the published four-item decisional-conflict screen (Legare et al., 2010), used here in
  the team's adapted wording. It is NOT validated in Hindi or Arabic. Its authors make it available
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
                "hi": "वाहक होने का आमतौर पर मतलब है...",
            },
            {
                "en": [
                    "You have the condition",
                    "You carry one changed copy, which usually doesn't cause illness",
                    "Your children will have the condition",
                ],
                "hi": [
                    "आपको वह बीमारी है",
                    "आपमें एक बदली हुई प्रति है, जिससे आमतौर पर बीमारी नहीं होती",
                    "आपके बच्चों को वह बीमारी होगी",
                ],
            },
            1,
        ),
        Item(
            "tb2",
            {
                "en": "Can a carrier pass the change on to a child?",
                "hi": "क्या वाहक बच्चे को यह बदलाव दे सकता है?",
            },
            {
                "en": ["Yes, a child may inherit one copy", "No, never", "Only to sons"],
                "hi": ["हाँ, बच्चे को एक प्रति मिल सकती है", "नहीं, कभी नहीं", "सिर्फ बेटों को"],
            },
            0,
        ),
        Item(
            "tb3",
            {
                "en": "Does an earlier pregnancy change the chance for the next one?",
                "hi": "क्या पिछली गर्भावस्था अगली की संभावना बदल देती है?",
            },
            {
                "en": [
                    "Yes, the chance goes down after an affected child",
                    "No, each pregnancy has the same chance",
                    "Yes, the chance goes up each time",
                ],
                "hi": [
                    "हाँ, प्रभावित बच्चे के बाद संभावना घट जाती है",
                    "नहीं, हर गर्भावस्था में वही संभावना रहती है",
                    "हाँ, हर बार संभावना बढ़ जाती है",
                ],
            },
            1,
        ),
        Item(
            "tb4",
            {
                "en": "If a screening test finds nothing shared, is there any chance left?",
                "hi": "अगर जाँच में कुछ साझा नहीं मिला, तो क्या कोई संभावना बचती है?",
            },
            {
                "en": [
                    "The test was wrong",
                    "No chance at all",
                    "Some chance remains, because no test finds every change",
                ],
                "hi": [
                    "जाँच गलत थी",
                    "कोई संभावना नहीं",
                    "कुछ संभावना रहती है, क्योंकि कोई भी जाँच हर बदलाव नहीं पकड़ती",
                ],
            },
            2,
        ),
        Item(
            "tb5",
            {
                "en": "Who decides what to do with this information?",
                "hi": "इस जानकारी के साथ क्या करना है, यह कौन तय करता है?",
            },
            {
                "en": ["You, with support if you want it", "The app", "Your family"],
                "hi": ["आप, और चाहें तो सहायता के साथ", "ऐप", "आपका परिवार"],
            },
            0,
        ),
    ),
)

SURE = InstrumentDef(
    key=Instrument.SURE,
    status="adapted, not validated in Hindi or Arabic",
    citation="Legare F, et al. Can Fam Physician 2010;56(8):e308-14 (the SURE test)",
    items=tuple(
        Item(key, text, {"en": ["Yes", "No"], "hi": ["हाँ", "नहीं"]}, None)
        for key, text in (
            (
                "s1",
                {
                    "en": "Do you feel sure about what is right for you?",
                    "hi": "क्या आपको भरोसा है कि आपके लिए क्या सही है?",
                },
            ),
            (
                "s2",
                {
                    "en": "Do you know the benefits and risks of each option?",
                    "hi": "क्या आप हर विकल्प के फायदे और जोखिम जानते हैं?",
                },
            ),
            (
                "s3",
                {
                    "en": "Are you clear about which benefits and risks matter most to you?",
                    "hi": "क्या आपको साफ़ है कि आपके लिए कौन से फायदे और जोखिम सबसे ज़्यादा मायने रखते हैं?",
                },
            ),
            (
                "s4",
                {
                    "en": "Do you have enough support to make a choice?",
                    "hi": "क्या आपके पास फ़ैसला लेने के लिए पर्याप्त सहायता है?",
                },
            ),
        )
    ),
)

OFFERED: dict[Instrument, InstrumentDef] = {
    Instrument.TEACH_BACK: TEACH_BACK,
    Instrument.SURE: SURE,
}


def language_for(language: str) -> str:
    return language if language in ("en", "hi") else "en"
