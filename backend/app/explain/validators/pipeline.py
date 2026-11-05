from dataclasses import dataclass, field

from app.explain.validators import rules
from app.explain.validators.text import has_arabic_script

# These stop an answer. Readability only notes a problem for the safety dashboard.
BLOCKING = frozenset({"directive", "certainty", "stigma", "number", "binding", "unknown_fact", "unreadable_script"})


@dataclass(frozen=True, slots=True)
class ValidationResult:
    flags: tuple[rules.Flag, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not any(flag.rule in BLOCKING for flag in self.flags)

    @property
    def names(self) -> list[str]:
        """What's stored with the message: which rules fired, never the text that fired them."""
        return sorted({flag.rule for flag in self.flags})


def validate_draft(
    text: str, language: str, level: str, labels: dict[str, str]
) -> ValidationResult:
    """Checks a draft before its placeholders are filled. Any failure means the template is used."""
    flags: list[rules.Flag] = []
    # Nothing here can read Arabic script yet, and text that can't be checked can't be shown.
    if has_arabic_script(text):
        flags.append(rules.Flag("unreadable_script"))
    flags += rules.directive(text, language)
    flags += rules.certainty(text, language)
    flags += rules.stigma(text, language)
    flags += rules.free_numbers(text, language)
    flags += rules.bindings(text, language, labels)
    flags += rules.readability(text, level)
    return ValidationResult(tuple(flags))
