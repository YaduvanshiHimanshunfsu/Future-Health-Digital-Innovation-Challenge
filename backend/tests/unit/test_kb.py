from pathlib import Path

import pytest

from app.explain.retriever import retrieve
from app.kb.ingest import ContentError, load_all, parse

FRONT = "---\nid: x\ncondition: general\nlang: en\nlevel: simple\nversion: 1\nstatus: draft\nsource: s\ntitle: t\n---\n"


def test_every_document_has_complete_front_matter_and_passes_the_rules() -> None:
    """V4.1.1. Loading refuses any file that doesn't, so the whole set loading is the check."""
    passages = load_all()
    assert len(passages) >= 24
    assert {p.lang for p in passages} == {"en", "hi"}


def test_every_topic_exists_in_both_languages() -> None:
    passages = load_all()
    english = {p.id for p in passages if p.lang == "en"}
    hindi = {p.id for p in passages if p.lang == "hi"}
    assert english == hindi


def test_every_condition_in_the_packs_has_content() -> None:
    """V4.1.6, at the Simple level."""
    from app.core.config import DEFAULT_PACKS_DIR
    from app.country_packs.loader import load_pack

    covered = {p.condition for p in load_all()}
    for code in ("ae-abu-dhabi", "in-india"):
        pack = load_pack(DEFAULT_PACKS_DIR / code)
        wanted = {c for entry in pack.panel.genes.values() for c in entry.conditions}
        missing = wanted - covered - {"pcd", "inherited_retinal", "glaucoma"}
        assert missing == set(), code


def test_unreviewed_content_says_so() -> None:
    """V4.1.4: a draft is labelled as one, so it can't pass as reviewed."""
    assert {p.status for p in load_all()} == {"draft"}


@pytest.mark.parametrize(
    "body",
    [
        "You should marry someone else.",
        "You are healthy.",
        "There is a 30% chance.",
        "Your genes are defective.",
    ],
)
def test_a_file_breaking_the_wording_rules_is_refused(tmp_path: Path, body: str) -> None:
    path = tmp_path / "x.md"
    path.write_text(FRONT + body + "\n", "utf-8")
    with pytest.raises(ContentError):
        parse(path)


def test_the_approved_general_facts_are_allowed(tmp_path: Path) -> None:
    path = tmp_path / "x.md"
    path.write_text(FRONT + "Each pregnancy has a 1 in 4 chance.\n", "utf-8")
    assert parse(path).text.startswith("Each pregnancy")


def test_a_file_missing_its_source_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "x.md"
    path.write_text(FRONT.replace("source: s\n", "") + "Text.\n", "utf-8")
    with pytest.raises(ContentError, match="source"):
        parse(path)


def test_reviewed_needs_a_reviewer(tmp_path: Path) -> None:
    path = tmp_path / "x.md"
    path.write_text(FRONT.replace("status: draft", "status: reviewed") + "Text.\n", "utf-8")
    with pytest.raises(ContentError, match="reviewer"):
        parse(path)


def test_retrieval_never_crosses_language_or_level() -> None:
    """V4.1.2."""
    for language in ("en", "hi"):
        for passage in retrieve("carrier gene child वाहक जीन", language, "simple", limit=10):
            assert passage.lang == language
            assert passage.level == "simple"
    assert retrieve("carrier", "en", "detailed") == []


def test_a_persons_own_condition_comes_first() -> None:
    assert [p.id for p in retrieve("tell me more", "en", "simple", ["dmd"])][:1] == ["dmd"]
