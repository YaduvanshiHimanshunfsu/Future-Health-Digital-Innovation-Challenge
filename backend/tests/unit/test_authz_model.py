import json
import re
from pathlib import Path

from app.ops.bootstrap_openfga import MODEL_FILE

DSL_FILE = Path(__file__).resolve().parents[3] / "infra" / "openfga" / "model.fga"


def relations_in_dsl() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    current: str | None = None
    for line in DSL_FILE.read_text("utf-8").splitlines():
        if line.startswith("type "):
            current = line.split()[1]
            found[current] = set()
        elif (match := re.match(r"\s+define (\w+):", line)) and current:
            found[current].add(match[1])
    return found


def test_the_readable_model_and_the_loaded_model_agree() -> None:
    loaded = json.loads(MODEL_FILE.read_text("utf-8"))
    relations = {item["type"]: set(item["relations"]) for item in loaded["type_definitions"]}
    assert relations == relations_in_dsl()


def test_every_grant_goes_through_an_expiring_tuple() -> None:
    """A share with no expiry could outlive the consent. Only "holder" takes a user directly here."""
    loaded = json.loads(MODEL_FILE.read_text("utf-8"))
    grant = next(item for item in loaded["type_definitions"] if item["type"] == "grant")
    assert grant["metadata"]["relations"]["holder"]["directly_related_user_types"] == [
        {"type": "user", "condition": "not_expired"}
    ]
    report = next(item for item in loaded["type_definitions"] if item["type"] == "report")
    for relation in ("summary_grant", "full_grant"):
        assert report["metadata"]["relations"][relation]["directly_related_user_types"] == [
            {"type": "grant", "relation": "holder"}
        ]
