"""Phrases each validator looks for, per language.

English is written by the team and needs review. Arabic appears here only
in Roman letters, as people often type it, with the meaning beside each one. Arabic script waits on the
user's approval and a reviewer (CLAUDE.md, rule 5). Until then, text in Arabic script never passes
these checks: see `ValidationResult` in pipeline.py.
"""

import re

from app.explain.validators.text import normalise

Patterns = dict[str, list[re.Pattern[str]]]


def _compile(table: dict[str, list[str]]) -> Patterns:
    # Patterns go through the same normal form as the text they're matched against.
    return {
        lang: [re.compile(normalise(item), re.IGNORECASE) for item in items]
        for lang, items in table.items()
    }


# Telling someone what to decide. Options are theirs to weigh.
DIRECTIVE = _compile(
    {
        "en": [
            r"\byou (should|ought to|must|need to)\b",
            r"\b(it would be|it'?s) (best|better|wise|safer) (to|if)\b",
            r"\b(we|i) (strongly )?(recommend|advise|suggest that you)\b",
            r"\b(best|right|correct|wrong) (option|choice|decision)\b",
            r"\b(don'?t|do not|never) (marry|get married|have (children|kids|a baby)|conceive)\b",
            r"\bbetter not to\b",
            r"\bthe (sensible|responsible) thing\b",
        ],
        # lazim (must), yajib (it is obligatory), ahsan lak (better for you), la tatazawaj (don't marry),
        # ansahak (I advise you), mafrood (supposed to).
        "ar": [
            r"\blazim\b",
            r"\byajib\b",
            r"\bahsan\s?lak\b",
            r"\bla\s?tatazawaj",
            r"\bansahak\b",
            r"\bmafrood\b",
        ],
    }
)

# False certainty, and saying what someone has or will have.
CERTAINTY = _compile(
    {
        "en": [
            r"\byou('?re| are) (healthy|fine|safe|normal|ok|okay|in the clear)\b",
            r"\b(there is|there'?s|you have|you are at) no risk\b",
            r"\bnothing to worry about\b",
            r"\b(guarantee[ds]?|definitely|certainly)\b",
            r"\b100 ?(%|per ?cent)",
            r"\byour (child|baby|children|kids) (will|would) (have|be|get|develop)\b",
            r"\byou (have|suffer from|are suffering from) (the )?(disease|condition|illness|thalass\w*|sickle cell)\b",
        ],
        # anta salim (you are healthy), ma fi khatar (there's no danger), akeed (certainly),
        # sayusab (will be afflicted).
        "ar": [r"\banta?\s?salim\b", r"\bma\s?fi\s?khatar\b", r"\bakeed\b", r"\bsayusab"],
    }
)

# Stigmatising words for people or genes.
STIGMA = _compile(
    {
        "en": [
            r"\b(defective|faulty|bad|abnormal|broken) (gene|genes|dna|blood|child|children)\b",
            r"\b(genes?|dna|blood) (is|are) (defective|faulty|bad|broken|abnormal)\b",
            r"\bincompatible\b",
            r"\b(suffers?|suffering) from\b",
            r"\bvictims?\b",
            r"\b(will|would|might) be affected\b",
            r"\bdeformed\b",
        ],
        # mush mutawafiq (incompatible), dam fasid (corrupt blood), atfal mareedin (sick children).
        "ar": [r"\bmush\s?mutawafiq", r"\bdam\s?fasid\b", r"\bmareed"],
    }
)

# Words that stand for numbers, so a number can't slip in spelled out.
NUMBER_WORDS = _compile(
    {
        "en": [
            # Counting copies, genes or chromosomes describes biology, not a chance, so it's allowed.
            r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand)\b"
            r"(?!\s+((changed|working|altered|extra)\s+)?(cop(y|ies)|genes?|parents?|partners?"
            r"|x\b|x chromosomes?|chromosomes?|from each|of (you|them|the|your)))",
            r"\b(half|quarter|third|most|majority|all) of (your|the|their) (children|kids|babies|pregnancies)\b",
            r"\bper ?cent\b",
        ],
        # nisf (half), rub' (quarter), thuluth (third), wahid min (one in), bil-mia (per cent).
        "ar": [r"\bnisf\b", r"\brub3?\b", r"\bthuluth\b", r"\bwahid\s?min\b", r"\bbil\s?mi"],
    }
)

# What each fact label is about, so a number can be checked against the words around it (issue C5).
LABEL_WORDS = {
    "en": {
        "two_copies": r"\b(two copies|both copies|two changed copies|inherits? two)\b",
        "carrier": r"\b(carriers?|one copy|one changed copy)\b",
        "neither": r"\b(neither|no changed cop|not inherit)\w*",
        "son_affected": r"\bsons?\b",
        "daughter_carrier": r"\bdaughters?\b",
        "daughter_two_copies": r"\bdaughters?\b",
        "daughter_neither": r"\bdaughters?\b",
    },
}
