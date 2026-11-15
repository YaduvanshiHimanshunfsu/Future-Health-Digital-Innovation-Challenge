import re
import unicodedata

# Roman-letter Arabic uses apostrophes and digits for some sounds (3 for ain, 7 for ha), and people
# type it many ways. These steps make "La2zim", "lazim" and "laazim" compare alike.
_REPEATS = re.compile(r"(.)\1+")
_SENTENCE_END = re.compile(r"(?<=[.!?\u0964])\s+")


_NUKTA = "\u093c"


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold().replace(_NUKTA, "")
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn" or _keep(c)
    )
    return unicodedata.normalize("NFC", text)


def _keep(character: str) -> bool:
    # Devanagari vowel signs and virama are marks too, and removing them would change the word.
    return "\u0900" <= character <= "\u097f"


def loose(text: str) -> str:
    """For Roman-letter Arabic only: drops apostrophes and collapses repeated letters."""
    return _REPEATS.sub(r"\1", normalise(text).replace("'", "").replace("\u2019", ""))


def sentences(text: str) -> list[str]:
    return [part for part in _SENTENCE_END.split(text.strip()) if part]


def has_unread_script(text: str) -> bool:
    """True when the text has a letter in any script other than Latin, which no rule here reads."""
    return any(c.isalpha() and not unicodedata.name(c, "").startswith("LATIN") for c in text)


def has_arabic_script(text: str) -> bool:
    return any(
        "\u0600" <= c <= "\u06ff" or "\u0750" <= c <= "\u077f" or "\ufb50" <= c <= "\ufeff"
        for c in text
    )
