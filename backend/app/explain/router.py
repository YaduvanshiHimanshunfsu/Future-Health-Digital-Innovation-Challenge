"""Decides what kind of question this is, before anything tries to answer it.

Rules only, so the result is the same every time and can be tested. Where rules disagree, the most
careful reading wins: distress, then coercion, then clinical, then decisions, then education.

Education is never the default. A question is answered automatically only when it is recognisably
about the topics Samvid explains (TOPIC below). Anything else, such as "I don't want to live
anymore", which names no topic, goes to a person. The early evaluation showed why: with education as
the fallback, a third of the questions meant for a person were answered by the machine
(docs/evaluation/router_early_eval.md).
"""

import re
from dataclasses import dataclass

from app.explain.validators.text import has_unread_script, loose, normalise
from app.models.enums import Boundary

_ORDER = [Boundary.DISTRESS, Boundary.COERCION, Boundary.CLINICAL_ADVICE, Boundary.DECISION_SUPPORT]


def _rules(table: dict[str, list[str]]) -> dict[str, list[re.Pattern[str]]]:
    # Patterns go through the same normal form as the text, or accented letters could fail to match.
    return {
        lang: [re.compile(normalise(p), re.IGNORECASE) for p in items]
        for lang, items in table.items()
    }


# English by the team, awaiting review. Arabic in Roman letters only, with meanings.
DISTRESS = _rules(
    {
        "en": [
            r"\b(kill|hurt|harm) (myself|me)\b",
            r"\bsuicid",
            r"\bend (my|it all|my life)\b",
            r"\bwant to die\b",
            r"\bcan'?t (go on|cope|take (it|this) any ?more)\b",
            r"\bno (reason|point) (to|in) (live|living)\b",
            r"\bhopeless\b",
            r"\b(don'?t|do not) want to (live|be (here|alive)|exist|wake up)\b",
            r"\b(ending|end|take|taking) my (own )?life\b",
            r"\bthink(ing)? (about|of) (dying|death|ending|killing)\b",
            r"\b(better off|rather be) dead\b",
            r"\bself[- ]?harm",
        ],
        # abi amoot (I want to die), antahir (kill myself), ta3ban wa ma aqdar (exhausted and can't cope),
        # ma abgha/abi a'ish (I don't want to live), aqtul nafsi (kill myself), adhurr nafsi (hurt
        # myself), ya'is (despair), ma agdar atahammal (I can't bear it).
        "ar": [
            r"\babi\s?amot\b",
            r"\bantahir\b",
            r"\bma\s?aqdar\s?akamil\b",
            r"\bma\s?(abgha|abi|abaa?)\s?a'?i?sh\b",
            r"\b(aqtul|aqtel|agtel)\s?nafs",
            r"\b(adhurr?|adurr?|a'?dhi)\s?nafs",
            r"\bya'?is",
            r"\bma\s?a[gq]dar\s?atahamal",
        ],
    }
)
COERCION = _rules(
    {
        "en": [
            r"\b(forc|pressur)(e|es|ed|ing) me\b",
            r"\b(making|make|made) me (marry|test|share|get)\b",
            r"\bthreaten",
            r"\bwon'?t let me\b",
            r"\b(my|the) (family|parents|husband|wife|partner|in-?laws) (insist|demand)",
            r"\bshow (them|him|her) my result",
            r"\bagainst my will\b",
            r"\b(will|would|going to) (leave|divorce) me\b",
            r"\bleave me if\b",
            r"\bwon'?t marry me (unless|if)\b",
        ],
        # ghasban 3anni (against my will), yijburni (he forces me), yhaddidni (he threatens me),
        # yadghatoon (they pressure), talaq (divorce), ma yikhallini (won't let me).
        "ar": [
            r"\bghasban\b",
            r"\byijb[iu]r",
            r"\by?u?had+id",
            r"\btahdid\b",
            r"\b(daght|dughut|yadghat)",
            r"\btalaq\b",
            r"\bma\s?yikhal+ini\b",
        ],
    }
)
CLINICAL = _rules(
    {
        "en": [
            r"\bpregnan",
            r"\b\d+\s*(weeks?|months?)\s*(pregnant|along|gone)\b",
            r"\bmiscarr",
            r"\bsymptoms?\b",
            r"\btreat(ment|ed|ing)?\b",
            r"\bmedic(ine|ation)s?\b",
            r"\bdos(e|age)\b",
            r"\bdiagnos",
            r"\b(abortion|terminat|ultrasound|scan|bleeding|fever|pain)\b",
            r"\bis (my|the) (baby|child|son|daughter) (sick|ill|ok|okay|healthy)\b",
            r"\bam i (sick|ill|affected)\b",
            r"\bwhat (test|dose)\b",
            r"\b(do|does|did) (i|he|she|they|my \w+) have\b",
            r"\bif (i|he|she|we|they|my \w+) (have|has|had)\b",
            r"\b(have|has) (i|he|she) got\b",
            r"\b(amnio|cvs|nipt|prenatal|antenatal|trimester|expecting a baby|due date|due in)\b",
            r"\b(tired|fatigue|swelling|jaundice|pale|breathless|hurts?|aches?)\b",
            r"\bis it safe (to|for)\b",
            r"\btests? does (it|he|she|the baby) need\b",
            r"\btrying to (conceive|get pregnant)\b",
        ],
        # ana hamil fi al-shahr (I'm pregnant in the month...), janin (foetus), usbu' (week), dawa (medicine),
        # 3ilaj (treatment), marid (sick).
        # Also: haml (pregnancy), fahs (examination), ta'ban (tired), tuja'ni/alam (it hurts/pain),
        # 'indi marad (I have a disease), hal hiya/huwa (is it), mareedh (sick).
        "ar": [
            r"\bjanin\b",
            r"\b(shahr|ashur|usbu|asabi)\b",
            r"\b(dawa|3ilaj|ilaj)\b",
            r"\bmare?e?d+h?\b",
            r"\bhaml\b",
            r"\bfahs\b",
            r"\bta'?3?ban\b",
            r"\b(tuja'?ni|yuja'?ni|alam|waja')\b",
            r"\b'?3?indi\s?marad\b",
            r"\bhal (hiya|huwa|hu)\b",
        ],
    }
)
DECISION = _rules(
    {
        "en": [
            r"\b(what are|tell me) (my|our) options\b",
            r"\b(should|can) (we|i) (still )?(marry|have (children|kids|a baby))\b",
            r"\b(ivf|embryo|pgt|adopt|fostering|kafala|donor)\b",
            r"\bwhat (can|could) we do\b",
            r"\bdecide\b|\bdecision\b",
            r"\bshould (we|i) (still )?(get )?(marry|married|wed|go ahead|continue|cancel)\b",
            r"\bwhat would you do\b",
            r"\bin (our|my) (place|shoes|position)\b",
            r"\bis it (wrong|right|ok|okay) (to|for us to) (have|marry)\b",
        ],
        # khiyarat (options), nitazawaj (we marry), atfal (children), qarar (decision), law kint makanna
        # (if you were in our place), atfal al anabeeb (IVF), hal lazim n... (must we...).
        "ar": [
            r"\bkhiyar",
            r"\bni?t[aei]?zaw+aj\b",
            r"\bqarar\b",
            r"\bmakan(na|i)\b",
            r"\b(shu|aysh|esh) (bitsawi|tsawi|bit'?mal)\b",
            r"\banabeb\b",
            r"\bhal (lazim )?n[a-z]+ atfal\b",
            r"\bhal n(itzawaj|sawi)\b",
        ],
    }
)

# "hamil" means both "pregnant" and "carrier" in Arabic. Only a carrier context makes it education.
_HAMIL = re.compile(r"\bhami?l(a|ah)?\b")
_CARRIER_CONTEXT = re.compile(
    r"\bhamil(a|ah)?\s?(li|lil|l|al|bil)[\s-]?(jin|jen|marad|sifa|tafra|gene)|\b(naqil|naqila)\b|\bcarr?ier\b"
)
# "ana hamil" alone could be either, so it isn't a marker here. Without a clear carrier context it's
# still read as pregnancy below, which is the safer reading.
_PREGNANCY_CONTEXT = re.compile(r"\bhamil(a|ah)?\s?(fi|bi|min)\b|\bshahr|\busbu|\bjanin")


# What Samvid explains. Only questions that name one of these may get an automatic answer.
TOPIC = _rules(
    {
        "en": [
            r"\b(genes?|genetics?|dna|chromosomes?|variants?|mutations?|vus)\b",
            r"\b(carriers?|inherit\w*|heredit\w*|recessive|dominant|x-?linked)\b",
            r"\b(panel|screening|tests?|results?|reports?|copy|copies|changes?)\b",
            r"\b(conditions?|disease|disorder|thalass\w*|sickle|cystic|g6pd|sma|duchenne|dmd|hbb)\b",
            r"\b(chances?|risks?|odds|percent(ages?)?|likel(y|ihood)|in each pregnancy)\b",
            r"\b(related|cousins?|consanguin\w*|parents?|families|family|relatives?)\b",
            r"\b(child|children|kids?|sons?|daughters?|bab(y|ies)|couples?|partners?)\b",
            r"\b(privacy|private|data|share|shared|sharing|consent|counsell?or|options?)\b",
        ],
        "ar": [
            r"\b(jin|jen|jinat|wiratha|warath\w*|naqil\w*|mutanah+i)\b",
            r"\b(marad|amradh?|natija|natayij\w*|fahs|tahlil|lawha\w*|nisba\w*)\b",
            r"\b(thalas\w*|sickle|minjali\w*)\b",
            r"\b(aqarib|qarib|zawaj|atfal|tifl|walid\w*|usra|ahl)\b",
            r"\bmurtabit\b",
            r"\bhamil\w* (li|lil|al|bil)",
        ],
    }
)


@dataclass(frozen=True, slots=True)
class Route:
    boundary: Boundary
    reasons: tuple[str, ...]
    pregnant: bool = False


def _matches(table: dict[str, list[re.Pattern[str]]], text: str, roman: str, language: str) -> bool:
    for lang in {language, "en", "ar"}:
        target = roman if lang == "ar" else text
        if any(pattern.search(target) for pattern in table.get(lang, [])):
            return True
    return False


def route(question: str, language: str) -> Route:
    text, roman = normalise(question), loose(question)
    # The rules read English, and Arabic typed in Roman letters. Anything in another script, Arabic
    # script included, is read by a person: a rule that can't read a question must not answer it.
    if has_unread_script(question):
        return Route(Boundary.CLINICAL_ADVICE, ("unsupported_script",))

    found: dict[Boundary, str] = {}
    if _matches(DISTRESS, text, roman, language):
        found[Boundary.DISTRESS] = "distress"
    if _matches(COERCION, text, roman, language):
        found[Boundary.COERCION] = "coercion"
    pregnant = False
    # Without a clear carrier context, "hamil" is read as pregnancy, the safer of the two.
    if _HAMIL.search(roman) and (
        _PREGNANCY_CONTEXT.search(roman) or not _CARRIER_CONTEXT.search(roman)
    ):
        found[Boundary.CLINICAL_ADVICE] = "pregnancy"
        pregnant = True
    if _matches(CLINICAL, text, roman, language):
        found.setdefault(Boundary.CLINICAL_ADVICE, "clinical")
        pregnant = pregnant or bool(re.search(r"pregnan|janin", text + roman))
    if _matches(DECISION, text, roman, language):
        found[Boundary.DECISION_SUPPORT] = "decision"

    for boundary in _ORDER:
        if boundary in found:
            return Route(boundary, tuple(found.values()), pregnant)
    if _matches(TOPIC, text, roman, language):
        return Route(Boundary.EDUCATION, ("education",))
    # Not recognisably about what Samvid explains, so nothing here can be sure it's safe to answer.
    return Route(Boundary.CLINICAL_ADVICE, ("unclear",))
