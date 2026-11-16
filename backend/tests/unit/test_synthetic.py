from pathlib import Path

import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.ingestion.fhir_parser import parse_report
from app.risk_engine.types import Scenario
from synthetic.generate import (
    build_bundle,
    generate,
    generate_population,
    load_personas,
    tree_digest,
)

PACKS = ["ae-abu-dhabi"]


def test_same_seed_gives_identical_output(tmp_path: Path) -> None:
    """V2.2.1."""
    first, second = tmp_path / "first", tmp_path / "second"
    for pack in PACKS:
        generate(first, pack, 200, 7, DEFAULT_PACKS_DIR)
        generate(second, pack, 200, 7, DEFAULT_PACKS_DIR)
    assert tree_digest(first) == tree_digest(second)


def test_different_seed_gives_different_output(tmp_path: Path) -> None:
    generate(tmp_path / "a", "ae-abu-dhabi", 200, 1, DEFAULT_PACKS_DIR)
    generate(tmp_path / "b", "ae-abu-dhabi", 200, 2, DEFAULT_PACKS_DIR)
    assert tree_digest(tmp_path / "a") != tree_digest(tmp_path / "b")


def test_each_scenario_appears_in_the_abu_dhabi_personas(tmp_path: Path) -> None:
    """V2.2.2. Every rule the engine has is reachable from a named demo person."""
    report = generate(tmp_path, "ae-abu-dhabi", 20, 1, DEFAULT_PACKS_DIR)
    assert set(report["persona_scenarios"]) == {scenario.value for scenario in Scenario}


def test_random_population_reaches_the_common_scenarios() -> None:
    pack = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
    panel, _, _ = load_personas("ae-abu-dhabi")
    _, summary = generate_population(pack, panel, 4000, 11)
    for scenario in (Scenario.COUPLE_SHARED_AR, Scenario.UNCERTAIN_VUS, Scenario.XL_FATHER):
        assert summary["scenarios"][scenario.value] > 0


@pytest.mark.parametrize("pack_code", PACKS)
def test_personas_exist_for_both_packs(pack_code: str) -> None:
    """V2.2.7."""
    _, people, couples = load_personas(pack_code)
    assert len(people) >= 5
    assert couples


@pytest.mark.parametrize("pack_code", PACKS)
def test_persona_ids_are_obviously_fake_and_match_the_pack(pack_code: str) -> None:
    """V2.2.3. An all-zero block can't belong to anyone."""
    import re

    pack = load_pack(DEFAULT_PACKS_DIR / pack_code)
    _, people, _ = load_personas(pack_code)
    pattern = re.compile(pack.identity.national_id_pattern)
    for person in people.values():
        assert pattern.fullmatch(person.national_id)
        assert "0000" in person.national_id


@pytest.mark.parametrize("pack_code", PACKS)
def test_observed_carrier_rates_are_close_to_the_table(pack_code: str) -> None:
    """V2.2.4. Within four standard errors, so this is a real check that won't flake."""
    pack = load_pack(DEFAULT_PACKS_DIR / pack_code)
    panel, _, _ = load_personas(pack_code)
    people = 8000
    _, summary = generate_population(pack, panel, people, 20261120)
    for gene, rates in summary["carrier_rates"].items():
        q = rates["table"]
        allowed = 4 * (q * (1 - q) / (people // 2)) ** 0.5 + 0.001
        assert abs(rates["observed"] - q) <= allowed, gene


@pytest.mark.parametrize("pack_code", PACKS)
def test_every_persona_bundle_passes_the_real_parser(pack_code: str) -> None:
    pack = load_pack(DEFAULT_PACKS_DIR / pack_code)
    panel, people, _ = load_personas(pack_code)
    for person in people.values():
        parsed = parse_report(
            build_bundle(person, pack, panel),
            national_id_system=pack.identity.national_id_fhir_system,
        )
        assert parsed.findings == person.findings
        assert parsed.sex == person.sex


@pytest.mark.parametrize("pack_code", PACKS)
def test_every_bundle_is_labelled_as_test_data(pack_code: str) -> None:
    pack = load_pack(DEFAULT_PACKS_DIR / pack_code)
    panel, people, _ = load_personas(pack_code)
    for person in people.values():
        assert build_bundle(person, pack, panel)["meta"]["security"][0]["code"] == "HTEST"


def test_panel_files_declare_placeholder_values() -> None:
    """V2.2.5."""
    for pack_code in PACKS:
        pack = load_pack(DEFAULT_PACKS_DIR / pack_code)
        assert pack.panel.values_status == "placeholder"
        assert all(entry.source == "placeholder" for entry in pack.panel.genes.values())
        text = (DEFAULT_PACKS_DIR / pack_code / "panel.yaml").read_text("utf-8")
        assert text.startswith("# PLACEHOLDER VALUES")


def test_abu_dhabi_gene_table_covers_the_common_conditions() -> None:
    pack = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
    covered = {condition for entry in pack.panel.genes.values() for condition in entry.conditions}
    assert {"cah", "inherited_retinal", "pcd", "beta_thal", "sickle_cell", "glaucoma"} <= covered
