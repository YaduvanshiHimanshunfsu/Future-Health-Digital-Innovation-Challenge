import re
import shutil
from pathlib import Path

import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.core.logging import scrub
from app.country_packs.loader import PackError, load_pack, load_registry
from app.country_packs.schema import Legal
from app.risk_engine.engine import person_facts
from app.risk_engine.types import Classification, Finding, Scenario, Sex, Zygosity

APP_DIR = Path(__file__).resolve().parents[2] / "app"
ABU_DHABI = DEFAULT_PACKS_DIR / "ae-abu-dhabi"
TEMPLATE = DEFAULT_PACKS_DIR / "_template"


def copy_pack(tmp_path: Path, source: Path = ABU_DHABI, name: str = "ae-abu-dhabi") -> Path:
    target = tmp_path / name
    shutil.copytree(source, target)
    return target


def replace_in(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    assert old in text
    path.write_text(text.replace(old, new), "utf-8")


def other_country(tmp_path: Path) -> Path:
    """A second, deliberately different country, built from the template.

    Abu Dhabi is the only country the prototype ships, so the checks that a setting is read from
    the pack rather than fixed in code need somewhere else to switch to. The template is it: every
    setting below differs from Abu Dhabi's, and keeping it loadable is worth testing anyway,
    because it is what anyone adding a country starts from.
    """
    pack = copy_pack(tmp_path, TEMPLATE, "xx-your-country")
    (pack / "strata.yaml").write_text(
        "regions: [north, south]\nage_bands: [18-24, 25+]\ngenders: [woman, man]\n"
        "sla_hours: {P1: 12, P2: 36, P3: 96, P4: 200}\n",
        "utf-8",
    )
    return pack


def test_the_shipped_pack_and_the_template_load(tmp_path: Path) -> None:
    assert load_pack(ABU_DHABI).code == "ae-abu-dhabi"
    assert load_pack(other_country(tmp_path)).code == "xx-your-country"


def test_switching_pack_changes_settings_with_no_code_change(tmp_path: Path) -> None:
    """V2.6.1."""
    abu_dhabi, other = load_pack(ABU_DHABI), load_pack(other_country(tmp_path))
    assert abu_dhabi.manifest.languages != other.manifest.languages
    assert {o.key for o in abu_dhabi.options.options} != {o.key for o in other.options.options}
    assert abu_dhabi.identity.national_id_label != other.identity.national_id_label
    assert abu_dhabi.services.qualified_human != other.services.qualified_human
    assert abu_dhabi.gene_table.genes != other.gene_table.genes


def test_abu_dhabi_pack_lists_no_donor_or_adoption_option() -> None:
    """S5: sources report these as unavailable there."""
    keys = {option.key for option in load_pack(ABU_DHABI).options.options}
    assert "fostering" in keys
    assert not keys & {"donor", "adoption"}


def test_same_finding_differs_only_through_the_pack(tmp_path: Path) -> None:
    """V2.6.2. A gene missing from a pack gives no number, and goes to a person."""
    finding = Finding("ABCA4", Classification.PATHOGENIC, Zygosity.HETEROZYGOUS)
    carried = person_facts([finding], Sex.FEMALE, load_pack(ABU_DHABI).gene_table)
    referred = person_facts([finding], Sex.FEMALE, load_pack(other_country(tmp_path)).gene_table)
    assert carried[0].scenario is Scenario.CARRIER_SELF
    assert referred[0].scenario is Scenario.REFER
    assert referred[0].value is None


@pytest.mark.parametrize(
    ("file", "line"),
    [
        ("pack.yaml", "disable_validators: true"),
        ("legal.yaml", "skip_consent: true"),
        ("legal.yaml", "allow_directive_language: true"),
        ("services.yaml", "ai_may_replace_counsellor: true"),
        ("strata.yaml", "safety_rules_off: true"),
    ],
)
def test_a_pack_cannot_switch_off_a_safety_rule(tmp_path: Path, file: str, line: str) -> None:
    """V2.6.3. No such setting exists, and anything unrecognised stops the pack loading."""
    pack = copy_pack(tmp_path)
    with (pack / file).open("a", encoding="utf-8") as handle:
        handle.write(f"\n{line}\n")
    with pytest.raises(PackError, match="invalid"):
        load_pack(pack)


def test_unreviewed_pack_is_refused_in_production() -> None:
    """V2.6.4."""
    with pytest.raises(PackError, match="production"):
        load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi"], "ae-abu-dhabi", production=True)


def test_unreviewed_pack_loads_for_a_demo_and_is_labelled() -> None:
    registry = load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi"], "ae-abu-dhabi", production=False)
    assert registry.default.manifest.status.value == "reference"
    assert not registry.default.is_reviewed


def drop_demo_centres(pack: Path) -> None:
    # A pack going for review has its invented centres taken out first; the loader insists on it.
    (pack / "services.yaml").write_text(
        "qualified_human: counsellor\ncentres: []\nfunding_notes: []\n", "utf-8"
    )


def test_reviewed_status_with_no_named_reviewer_is_still_refused(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    drop_demo_centres(pack)
    replace_in(pack / "pack.yaml", "status: reference", "status: reviewed")
    with pytest.raises(PackError, match="production"):
        load_registry(tmp_path, ["ae-abu-dhabi"], "ae-abu-dhabi", production=True)


def test_reviewed_pack_with_a_named_reviewer_runs_in_production(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    drop_demo_centres(pack)
    replace_in(pack / "pack.yaml", "status: reference", "status: reviewed")
    replace_in(pack / "pack.yaml", "reviewers: []", "reviewers: [Dr Example]")
    registry = load_registry(tmp_path, ["ae-abu-dhabi"], "ae-abu-dhabi", production=True)
    assert registry.default.is_reviewed


def test_no_country_specific_values_in_application_code() -> None:
    """V2.6.5. Stubs for later phases are skipped until they hold real code."""
    banned = re.compile(r"Emirates|Abu Dhabi|\bUAE\b|\+971|\b784\b|Malaffi|Al Amal|ABHA|\bIndia\b")
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        text = path.read_text("utf-8")
        if "STATUS: STUB" not in text and banned.search(text):
            offenders.append(path.relative_to(APP_DIR).as_posix())
    assert offenders == []


def test_no_qualified_service_is_stated_and_not_assumed(tmp_path: Path) -> None:
    """V2.6.6. The screens use this to say nothing is listed, instead of implying a service."""
    other = load_pack(other_country(tmp_path))
    assert other.services.qualified_human == "none"
    assert other.services.centres == []


def test_a_demo_centre_can_never_send_anyone_anywhere() -> None:
    """An invented centre has no phone, website or check date, so it can't pass for a real one."""
    assert load_pack(ABU_DHABI).services.centres
    for centre in load_pack(ABU_DHABI).services.centres:
        assert centre.fictional
        assert (centre.contact, centre.source_url, centre.checked_on) == (None, None, None)


TEST_ENTRY = """
  - id: ae-test-entry
    fictional: true
    name: Test Clinic
    city: Abu Dhabi
    region: abu-dhabi
    kind: community_clinic
    services: [genetic_counselling]
    modes: [in_person]
    lat: 24.4
    lon: 54.4
"""


def add_centre(pack: Path, entry: str) -> None:
    replace_in(pack / "services.yaml", "\nfunding_notes:", f"{entry}\nfunding_notes:")


@pytest.mark.parametrize(
    ("old", "new"),
    [
        # A phone number on an invented centre would send someone to a real one.
        ("    lon: 54.4\n", "    lon: 54.4\n    contact: 02 000 0000\n"),
        # A real centre must say where its details came from, and when they were checked.
        ("    fictional: true", "    fictional: false"),
        ("    region: abu-dhabi", "    region: dubai"),
        ("[genetic_counselling]", "[genetic_counselling, genetic_counselling]"),
        ("[genetic_counselling]", "[miracle_cure]"),
        ("id: ae-test-entry", "id: ae-abu-dhabi-nakhla"),
    ],
    ids=[
        "contact",
        "real-no-source",
        "unknown-region",
        "service-twice",
        "unknown-service",
        "same-id",
    ],
)
def test_a_centre_that_breaks_a_rule_stops_the_pack(tmp_path: Path, old: str, new: str) -> None:
    pack = copy_pack(tmp_path)
    assert old in TEST_ENTRY
    add_centre(pack, TEST_ENTRY.replace(old, new))
    with pytest.raises(PackError):
        load_pack(pack)


def test_a_real_centre_with_its_source_loads(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    real = TEST_ENTRY.replace("fictional: true", "fictional: false")
    add_centre(
        pack, real + "    source_url: https://example.org/list\n    checked_on: '2026-11-15'\n"
    )
    loaded = load_pack(pack)
    assert [c.id for c in loaded.services.centres if not c.fictional] == ["ae-test-entry"]


def test_a_reviewed_pack_cannot_list_fictional_centres(tmp_path: Path) -> None:
    """Once local reviewers sign a pack off, an invented centre in it would read as checked."""
    pack = copy_pack(tmp_path)
    replace_in(
        pack / "pack.yaml",
        "status: reference\nreviewers: []",
        "status: reviewed\nreviewers: [A Reviewer]",
    )
    with pytest.raises(PackError, match="fictional"):
        load_pack(pack)


def test_legal_defaults_are_the_most_restrictive() -> None:
    """V2.6.7."""
    defaults = Legal()
    assert defaults.data_may_leave_region is False
    assert defaults.health_record_retention_years is None
    assert defaults.licensed_partner_required is True
    assert defaults.sex_selection_restricted is True
    assert defaults.right_not_to_know is True


def test_missing_legal_file_gives_restrictive_rules(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    (pack / "legal.yaml").unlink()
    assert load_pack(pack).legal == Legal()


def test_strata_and_time_targets_come_from_the_pack(tmp_path: Path) -> None:
    """V2.6.8."""
    abu_dhabi, other = load_pack(ABU_DHABI), load_pack(other_country(tmp_path))
    assert abu_dhabi.strata.regions != other.strata.regions
    assert abu_dhabi.strata.sla_hours.P2 != other.strata.sla_hours.P2


def test_pack_identity_formats_are_scrubbed_from_logs() -> None:
    """Finishes V1.4.3: formats come from the pack, including ones the generic rules miss."""
    assert "ABCDE" in scrub("ref ABCDE-12")
    load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi"], "ae-abu-dhabi", production=False)
    assert "1234567" not in scrub("id 784-1990-1234567-1 in request")


@pytest.mark.parametrize("missing", ["pack.yaml", "panel.yaml", "identity.yaml"])
def test_required_files_must_exist(tmp_path: Path, missing: str) -> None:
    pack = copy_pack(tmp_path)
    (pack / missing).unlink()
    with pytest.raises(PackError, match="missing"):
        load_pack(pack)


def test_template_is_not_a_runnable_pack() -> None:
    with pytest.raises(PackError):
        load_pack(DEFAULT_PACKS_DIR / "_template")


def test_folder_and_code_must_match(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path, name="ae-other")
    with pytest.raises(PackError, match="match"):
        load_pack(pack)


def test_panel_cannot_list_a_gene_with_no_data(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    replace_in(pack / "panel.yaml", "[HBB, HBA1", "[NOTAGENE, HBB, HBA1")
    with pytest.raises(PackError, match="unknown genes"):
        load_pack(pack)


def test_invalid_identity_pattern_is_refused(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    (pack / "identity.yaml").write_text(
        "national_id_label: x\nnational_id_pattern: '('\nnational_id_fhir_system: urn:x\n", "utf-8"
    )
    with pytest.raises(PackError, match="pattern"):
        load_pack(pack)


def test_default_language_must_be_offered(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    replace_in(pack / "pack.yaml", "default_language: en", "default_language: fr")
    with pytest.raises(PackError, match="invalid"):
        load_pack(pack)


def test_yaml_cannot_run_code(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    (pack / "strata.yaml").write_text("regions: !!python/object/apply:os.getcwd []\n", "utf-8")
    with pytest.raises(PackError, match="invalid"):
        load_pack(pack)


def test_enabled_pack_must_exist() -> None:
    with pytest.raises(PackError, match="not found"):
        load_registry(DEFAULT_PACKS_DIR, ["zz-nowhere"], "zz-nowhere", production=False)


def test_default_pack_must_be_enabled() -> None:
    with pytest.raises(PackError, match="default pack"):
        load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi"], "zz-nowhere", production=False)


def test_registry_lookups() -> None:
    registry = load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi"], "ae-abu-dhabi", production=False)
    assert registry.codes == {"ae-abu-dhabi"}
    assert registry.get("zz") is None
    with pytest.raises(PackError):
        registry.require("zz")


def test_national_id_normalisation_uses_the_pack_rule() -> None:
    pack = load_pack(ABU_DHABI)
    assert pack.normalise_national_id("784-1990-1234567-1") == pack.normalise_national_id(
        "784199012345671"
    )


def test_a_variant_naming_a_condition_its_gene_cannot_cause_stops_the_pack(
    tmp_path: Path,
) -> None:
    pack = copy_pack(tmp_path)
    replace_in(pack / "panel.yaml", '"c.20A>T": sickle_cell', '"c.20A>T": cystic_fibrosis')
    with pytest.raises(PackError, match="invalid"):
        load_pack(pack)


def test_region_names_belong_to_the_pack_and_name_only_its_regions(tmp_path: Path) -> None:
    """A proper name such as "Al Ain" is country-specific, so it lives in the pack (rule 6)."""
    assert load_pack(ABU_DHABI).strata.region_names["al-ain"] == "Al Ain"
    pack = copy_pack(tmp_path)
    replace_in(pack / "strata.yaml", "al-dhafra: Al Dhafra}", "al-dhafra: Al Dhafra, dubai: Dubai}")
    with pytest.raises(PackError, match="invalid"):
        load_pack(pack)
