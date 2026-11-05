"""Decides what kind of question this is, before anything tries to answer it.

Rules only, so the result is the same every time and can be tested. Where rules disagree, the most
careful reading wins: distress, then coercion, then clinical, then decisions, then education.
"""

import re
from dataclasses import dataclass

from app.explain.validators.text import has_arabic_script, loose, normalise
from app.models.enums import Boundary

_ORDER = [Boundary.DISTRESS, Boundary.COERCION, Boundary.CLINICAL_ADVICE, Boundary.DECISION_SUPPORT]


def _rules(table: dict[str, list[str]]) -> dict[str, list[re.Pattern[str]]]:
    return {lang: [re.compile(p, re.IGNORECASE) for p in items] for lang, items in table.items()}


# English and Hindi by the team, awaiting native review. Arabic in Roman letters only, with meanings.
DISTRESS = _rules(
    {
        "en": [r"\b(kill|hurt|harm) (myself|me)\b", r"\bsuicid", r"\bend (my|it all|my life)\b", r"\bwant to die\b",
               r"\bcan'?t (go on|cope|take (it|this) any ?more)\b", r"\bno (reason|point) (to|in) (live|living)\b", r"\bhopeless\b"],
        "hi": [r"आत्महत्या", r"(मर|मरना) (जाना|चाहता|चाहती)", r"जीना नहीं", r"\b(khudkushi|aatmahatya)\b", r"\bmarna chah"],
        # abi amoot (I want to die), antahir (kill myself), ta3ban wa ma aqdar (exhausted and can't cope).
        "ar": [r"\babi\s?amot\b", r"\bantahir\b", r"\bma\s?aqdar\s?akamil\b"],
    }
)
COERCION = _rules(
    {
        "en": [r"\b(forc|pressur)(e|es|ed|ing) me\b", r"\b(making|make|made) me (marry|test|share|get)\b",
               r"\bthreaten", r"\bwon'?t let me\b", r"\b(my|the) (family|parents|husband|wife|partner|in-?laws) (insist|demand)",
               r"\bshow (them|him|her) my result", r"\bagainst my will\b"],
        "hi": [r"ज़?ज़बरदस्ती|जबरदस्ती", r"दबाव", r"मजबूर", r"धमकी", r"\b(zabardasti|majboor|dabav|dhamki)\b"],
        # ghasban 3anni (against my will), yijburni (he forces me), yhaddidni (he threatens me).
        "ar": [r"\bghasban\b", r"\byijburn", r"\byhad+idn", r"\bdaght\b"],
    }
)
CLINICAL = _rules(
    {
        "en": [r"\bpregnan", r"\b\d+\s*(weeks?|months?)\s*(pregnant|along|gone)\b", r"\bmiscarr", r"\bsymptoms?\b",
               r"\btreat(ment|ed|ing)?\b", r"\bmedic(ine|ation)s?\b", r"\bdos(e|age)\b", r"\bdiagnos",
               r"\b(abortion|terminat|ultrasound|scan|bleeding|fever|pain)\b", r"\bis (my|the) (baby|child|son|daughter) (sick|ill|ok|okay|healthy)\b",
               r"\bam i (sick|ill|affected)\b", r"\bwhat (test|dose)\b"],
        "hi": [r"गर्भवती", r"गर्भ में", r"(महीने|हफ्ते) (की|का|से)", r"लक्षण", r"इलाज", r"दवा", r"बीमार", r"गर्भपात",
               r"\b(garbhvati|pregnant|ilaaj|dawa|bimaar)\b"],
        # ana hamil fi al-shahr (I'm pregnant in the month...), janin (foetus), usbu' (week), dawa (medicine),
        # 3ilaj (treatment), marid (sick).
        "ar": [r"\bjanin\b", r"\b(shahr|ashhur|usbu|asabi)\b", r"\b(dawa|3ilaj|ilaj)\b", r"\bmarid\b"],
    }
)
DECISION = _rules(
    {
        "en": [r"\b(what are|tell me) (my|our) options\b", r"\b(should|can) (we|i) (still )?(marry|have (children|kids|a baby))\b",
               r"\b(ivf|embryo|pgt|adopt|fostering|kafala|donor)\b", r"\bwhat (can|could) we do\b", r"\bdecide\b|\bdecision\b"],
        "hi": [r"विकल्प", r"(शादी|विवाह) (कर|करें|करना)", r"बच्चे (पैदा|हो)", r"\b(vikalp|shaadi)\b", r"निर्णय|फैसला"],
        # khiyarat (options), nitazawaj (we marry), atfal (children), qarar (decision).
        "ar": [r"\bkhiyar", r"\bnitazawaj\b", r"\bqarar\b"],
    }
)

# "hamil" means both "pregnant" and "carrier" in Arabic. Only a carrier context makes it education.
_HAMIL = re.compile(r"\bhamil(a|ah)?\b")
_CARRIER_CONTEXT = re.compile(r"\bhamil(a|ah)?\s?(li|lil|l|al|bil)[\s-]?(jin|jeen|marad|sifa|tafra|gene)|\b(naqil|naqila)\b|\bcarrier\b")
_PREGNANCY_CONTEXT = re.compile(r"\b(ana|anti|inti|hiya|zawjti)\s?hamil|\bhamil\s?(fi|bi|min)\b|\bshahr|\busbu|\bjanin")


@dataclass(frozen=True, slots=True)
class Route:
    boundary: Boundary
    reasons: tuple[str, ...]
    pregnant: bool = False


def _matches(table: dict[str, list[re.Pattern[str]]], text: str, roman: str, language: str) -> bool:
    for lang in {language, "en", "hi", "ar"}:
        target = roman if lang == "ar" else text
        if any(pattern.search(target) for pattern in table.get(lang, [])):
            return True
    return False


def route(question: str, language: str) -> Route:
    text, roman = normalise(question), loose(question)
    # Nothing here can read Arabic script yet, so a person reads it. Never a guess.
    if has_arabic_script(question):
        return Route(Boundary.CLINICAL_ADVICE, ("unsupported_script",))

    found: dict[Boundary, str] = {}
    if _matches(DISTRESS, text, roman, language):
        found[Boundary.DISTRESS] = "distress"
    if _matches(COERCION, text, roman, language):
        found[Boundary.COERCION] = "coercion"
    pregnant = False
    if _HAMIL.search(roman):
        if _PREGNANCY_CONTEXT.search(roman) or not _CARRIER_CONTEXT.search(roman):
            # Without a clear carrier context, "hamil" is read as pregnancy, the safer of the two.
            found[Boundary.CLINICAL_ADVICE] = "pregnancy"
            pregnant = True
    if _matches(CLINICAL, text, roman, language):
        found.setdefault(Boundary.CLINICAL_ADVICE, "clinical")
        pregnant = pregnant or bool(re.search(r"pregnan|गर्भवती|garbhvati|janin", text + roman))
    if _matches(DECISION, text, roman, language):
        found[Boundary.DECISION_SUPPORT] = "decision"

    for boundary in _ORDER:
        if boundary in found:
            return Route(boundary, tuple(found.values()), pregnant)
    return Route(Boundary.EDUCATION, ("education",))
