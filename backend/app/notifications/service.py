"""Messages to people outside the app, such as a reminder.

They say only that there is something to look at in Samvid. Never a gene, a condition, a result, a
name or a reason (V5.2.4): a text message is read on a lock screen, by whoever holds the phone.

The prototype sends nothing: `MockNotifier` records what would have been sent. A real SMS or email
provider implements `Notifier` and receives the same short, fixed text.
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol

log = logging.getLogger(__name__)

# Fixed texts, one per purpose and language. Nothing is ever filled into them.
TEMPLATES: dict[str, dict[str, str]] = {
    "reminder": {
        "en": "You have a step waiting in Samvid. Open the app when it suits you. Reply STOP for no more reminders.",
    },
    "appointment": {
        "en": "Your appointment in Samvid has changed. Open the app to see the details.",
    },
}


class Notifier(Protocol):
    async def send(self, person_ref: str, purpose: str, language: str) -> None: ...


def text_for(purpose: str, language: str) -> str:
    texts = TEMPLATES[purpose]
    return texts.get(language, texts["en"])


@dataclass
class MockNotifier:
    """Records each message instead of sending it. `person_ref` is a pseudonym, never a number."""

    sent: list[tuple[str, str, str]] = field(default_factory=list)

    async def send(self, person_ref: str, purpose: str, language: str) -> None:
        text = text_for(purpose, language)
        self.sent.append((person_ref, purpose, text))
        log.info("notification_mocked", extra={"ctx": {"purpose": purpose, "lang": language}})
