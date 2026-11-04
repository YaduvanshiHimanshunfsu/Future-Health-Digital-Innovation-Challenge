import json
import logging
import re
import sys
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

# Keys whose values must never appear in a log line, whatever they hold.
SENSITIVE_KEYS = frozenset(
    {
        "answer",
        "authorization",
        "content",
        "cookie",
        "email",
        "gene",
        "hgvs",
        "message",
        "name",
        "national_id",
        "password",
        "phone",
        "question",
        "secret",
        "token",
    }
)

# Formats that hold in any country. \d also matches Devanagari and Arabic-Indic digits, so numbers
# typed in a local script are caught too. Country packs add their own patterns at start-up.
_BASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]*"), "[JWT]"),
    (re.compile(r"(?<![\w.])\+?\d(?:[\s-]?\d){7,}(?![\w.])"), "[NUMBER]"),
)

_extra_patterns: list[tuple[re.Pattern[str], str]] = []


def register_scrub_patterns(patterns: Iterable[tuple[str, str]]) -> None:
    """Add country-specific formats, such as a national ID layout, from the active pack."""
    _extra_patterns.extend((re.compile(pattern), label) for pattern, label in patterns)


def clear_scrub_patterns() -> None:
    _extra_patterns.clear()


def scrub(text: str) -> str:
    for pattern, label in _extra_patterns:
        text = pattern.sub(label, text)
    for pattern, label in _BASE_PATTERNS:
        text = pattern.sub(label, text)
    return text


def _scrub_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS:
        return "[REDACTED]"
    if isinstance(value, str):
        return scrub(value)
    if isinstance(value, Mapping):
        return {str(k): _scrub_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [_scrub_value(key, item) for item in value]
    if isinstance(value, bool | int | float) or value is None:
        return value
    return scrub(str(value))


class PhiSafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": scrub(record.getMessage()),
        }
        context = getattr(record, "ctx", None)
        if isinstance(context, Mapping):
            entry["ctx"] = {str(k): _scrub_value(str(k), v) for k, v in context.items()}
        if record.exc_info and record.exc_info[0] is not None:
            # Only the type. An exception's text or traceback can quote the data that caused it.
            entry["exc_type"] = record.exc_info[0].__name__
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PhiSafeJsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "celery"):
        named = logging.getLogger(name)
        named.handlers = []
        named.propagate = True
    # The access log prints raw paths and query strings, and invitation tokens travel in paths.
    logging.getLogger("uvicorn.access").disabled = True
