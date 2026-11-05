"""What a person said matters to them. Stored encrypted, reflected back, and never scored."""

import uuid

QUESTIONS = ("what_matters", "worries", "who_to_involve", "timing")
MAX_ANSWER = 500


def values_aad(note_id: uuid.UUID) -> str:
    return f"values_note:{note_id}:answers"
