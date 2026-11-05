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
INDIA = DEFAULT_PACKS_DIR / "in-india"


def copy_pack(tmp_path: Path, source: Path = ABU_DHABI, name: str = "ae-abu-dhabi") -> Path:
    target = tmp_path / name
    shutil.copytree(source, target)
    return target


def replace_in(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    assert old in text
    path.write_text(text.replace(old, new), "utf-8")


def test_both_shipped_packs_load() -> None:
    assert load_pack(ABU_DHABI).code == "ae-abu-dhabi"
    assert load_pack(INDIA).code == "in-india"


def test_switching_pack_changes_settings_with_no_code_change() -> None:
    """V2.6.1."""
    abu_dhabi, india = load_pack(ABU_DHABI), load_pack(INDIA)
    assert abu_dhabi.manifest.languages != india.manifest.languages
    assert {o.key for o in abu_dhabi.options.options} != {o.key for o in india.options.options}
    assert abu_dhabi.identity.national_id_label != india.identity.national_id_label
    assert abu_dhabi.services.qualified_human != india.services.qualified_human
    assert abu_dhabi.gene_table.genes != india.gene_table.genes


def test_abu_dhabi_pack_lists_no_donor_or_adoption_option() -> None:
    """S5: sources report these as unavailable there."""
    keys = {option.key for option in load_pack(ABU_DHABI).options.options}
    assert "fostering" in keys
    assert not keys & {"donor", "adoption"}


def test_same_finding_differs_only_through_the_pack() -> None:
    """V2.6.2. A gene missing from a pack gives no number, and goes to a person."""
    finding = Finding("ABCA4", Classification.PATHOGENIC, Zygosity.HETEROZYGOUS)
    carried = person_facts([finding], Sex.FEMALE, load_pack(ABU_DHABI).gene_table)
    referred = person_facts([finding], Sex.FEMALE, load_pack(INDIA).gene_table)
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


@pytest.mark.parametrize("code", ["ae-abu-dhabi", "in-india"])
def test_unreviewed_pack_is_refused_in_production(code: str) -> None:
    """V2.6.4."""
    with pytest.raises(PackError, match="production"):
        load_registry(DEFAULT_PACKS_DIR, [code], code, production=True)


def test_unreviewed_pack_loads_for_a_demo_and_is_labelled() -> None:
    registry = load_registry(DEFAULT_PACKS_DIR, ["in-india"], "in-india", production=False)
    assert registry.default.manifest.status.value == "illustrative"
    assert not registry.default.is_reviewed


def test_reviewed_status_with_no_named_reviewer_is_still_refused(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
    replace_in(pack / "pack.yaml", "status: reference", "status: reviewed")
    with pytest.raises(PackError, match="production"):
        load_registry(tmp_path, ["ae-abu-dhabi"], "ae-abu-dhabi", production=True)


def test_reviewed_pack_with_a_named_reviewer_runs_in_production(tmp_path: Path) -> None:
    pack = copy_pack(tmp_path)
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


def test_no_qualified_service_is_stated_and_not_assumed() -> None:
    """V2.6.6. The screens use this to say nothing is listed, instead of implying a service."""
    india = load_pack(INDIA)
    assert india.services.qualified_human == "none"
    assert india.services.centres == []


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


def test_strata_and_time_targets_come_from_the_pack() -> None:
    """V2.6.8."""
    abu_dhabi, india = load_pack(ABU_DHABI), load_pack(INDIA)
    assert abu_dhabi.strata.regions != india.strata.regions
    assert abu_dhabi.strata.sla_hours.P2 != india.strata.sla_hours.P2


def test_pack_identity_formats_are_scrubbed_from_logs() -> None:
    """Finishes V1.4.3: formats come from the pack, including ones the generic rules miss."""
    assert "ABCDE" in scrub("ref ABCDE-12")
    load_registry(DEFAULT_PACKS_DIR, ["ae-abu-dhabi", "in-india"], "ae-abu-dhabi", production=False)
    assert "1234567" not in scrub("id 784-1990-1234567-1 in request")
    assert "0000" not in scrub("abha 00-0000-0000-0001")


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
        load_registry(DEFAULT_PACKS_DIR, ["in-india"], "ae-abu-dhabi", production=False)


def test_registry_lookups() -> None:
    registry = load_registry(DEFAULT_PACKS_DIR, ["in-india"], "in-india", production=False)
    assert registry.codes == {"in-india"}
    assert registry.get("zz") is None
    with pytest.raises(PackError):
        registry.require("zz")


def test_national_id_normalisation_uses_the_pack_rule() -> None:
    pack = load_pack(ABU_DHABI)
    assert pack.normalise_national_id("784-1990-1234567-1") == pack.normalise_national_id(
        "784199012345671"
    )
