import json
from functools import lru_cache
from pathlib import Path

_MESSAGES_DIR = Path(__file__).parent / "messages"
FALLBACK_LANGUAGE = "en"


@lru_cache
def _catalogue(language: str) -> dict[str, str]:
    path = _MESSAGES_DIR / f"{language}.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        loaded: dict[str, str] = json.load(handle)
    return loaded


def translate(key: str, language: str) -> str:
    """Look up a message, falling back to English, and then to the key so nothing renders blank."""
    return _catalogue(language).get(key) or _catalogue(FALLBACK_LANGUAGE).get(key) or key


def negotiate_language(header: str | None, supported: list[str], default: str) -> str:
    """Pick the best supported language from an Accept-Language header."""
    if not header or len(header) > 256:
        return default
    ranked: list[tuple[float, int, str]] = []
    for position, part in enumerate(header.split(",")):
        tag, _, params = part.strip().partition(";")
        quality = 1.0
        if params.strip().startswith("q="):
            try:
                quality = float(params.strip()[2:])
            except ValueError:
                continue
        primary = tag.strip().split("-")[0].lower()
        if primary in supported and quality > 0:
            ranked.append((-quality, position, primary))
    return min(ranked)[2] if ranked else default
