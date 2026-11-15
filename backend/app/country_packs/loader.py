import re
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from app.core.logging import register_scrub_patterns
from app.country_packs.schema import (
    Identity,
    Legal,
    Lexicon,
    Manifest,
    OptionsFile,
    PackStatus,
    Panel,
    Services,
    Strata,
    SupportContacts,
)
from app.risk_engine.frequencies import GeneInfo, GeneTable
from app.risk_engine.types import Inheritance

_Model = TypeVar("_Model", bound=BaseModel)
# The frequency table only has so much precision. Anything finer would be false accuracy.
_MAX_DENOMINATOR = 1_000_000


class PackError(Exception):
    """A pack is missing, invalid, or not allowed to run here. Start-up stops rather than guess."""


@dataclass(frozen=True)
class CountryPack:
    manifest: Manifest
    options: OptionsFile
    legal: Legal
    panel: Panel
    services: Services
    support_contacts: SupportContacts
    identity: Identity
    lexicon: Lexicon
    strata: Strata

    @property
    def code(self) -> str:
        return self.manifest.code

    @property
    def is_reviewed(self) -> bool:
        return self.manifest.status is PackStatus.REVIEWED and bool(self.manifest.reviewers)

    @cached_property
    def gene_table(self) -> GeneTable:
        genes = {
            name: GeneInfo(
                gene=name,
                inheritance=Inheritance(entry.inheritance),
                carrier_frequency=Fraction(entry.carrier_frequency).limit_denominator(
                    _MAX_DENOMINATOR
                ),
                detection_rate=Fraction(entry.detection_rate).limit_denominator(_MAX_DENOMINATOR),
                conditions=tuple(entry.conditions),
                risk_group=entry.risk_group,
                routine_when_hemizygous=entry.routine_when_hemizygous,
            )
            for name, entry in self.panel.genes.items()
        }
        panels = {version: frozenset(genes_) for version, genes_ in self.panel.panels.items()}
        return GeneTable(genes, panels)

    def normalise_national_id(self, raw: str) -> str:
        return raw.translate({ord(char): None for char in self.identity.national_id_ignore}).strip()


def _read[Model: BaseModel](
    directory: Path, name: str, model: type[Model], *, required: bool = False
) -> Model:
    path = directory / name
    if not path.is_file():
        if required:
            raise PackError(f"{directory.name}: {name} is missing")
        return model()
    try:
        # safe_load, because a pack file must never be able to run anything.
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return model.model_validate(data)
    except (yaml.YAMLError, ValidationError) as exc:
        raise PackError(f"{directory.name}/{name} is invalid: {exc}") from exc


def load_pack(directory: Path) -> CountryPack:
    pack = CountryPack(
        manifest=_read(directory, "pack.yaml", Manifest, required=True),
        options=_read(directory, "options.yaml", OptionsFile),
        legal=_read(directory, "legal.yaml", Legal),
        panel=_read(directory, "panel.yaml", Panel, required=True),
        services=_read(directory, "services.yaml", Services),
        support_contacts=_read(directory, "support_contacts.yaml", SupportContacts),
        identity=_read(directory, "identity.yaml", Identity, required=True),
        lexicon=_read(directory, "lexicon.yaml", Lexicon),
        strata=_read(directory, "strata.yaml", Strata),
    )
    if pack.code != directory.name:
        raise PackError(f"{directory.name}: code {pack.code!r} doesn't match its folder")
    for version, genes in pack.panel.panels.items():
        unknown = set(genes) - set(pack.panel.genes)
        if unknown:
            raise PackError(f"{pack.code}: panel {version} lists unknown genes {sorted(unknown)}")
    try:
        re.compile(pack.identity.national_id_pattern)
        if pack.identity.phone_pattern:
            re.compile(pack.identity.phone_pattern)
    except re.error as exc:
        raise PackError(f"{pack.code}: invalid identity pattern") from exc
    _check_centres(pack)
    return pack


def _check_centres(pack: CountryPack) -> None:
    centres = pack.services.centres
    ids = [centre.id for centre in centres]
    if len(set(ids)) != len(ids):
        raise PackError(f"{pack.code}: two centres share an id")
    stray = {centre.region for centre in centres} - set(pack.strata.regions)
    if stray:
        raise PackError(f"{pack.code}: centres name regions it doesn't define: {sorted(stray)}")
    # Demo entries are for a pack still being drafted. Once local reviewers sign a pack off,
    # an invented centre in it would read as a checked one.
    if pack.manifest.status is PackStatus.REVIEWED and any(c.fictional for c in centres):
        raise PackError(f"{pack.code}: a reviewed pack cannot list fictional centres")


class PackRegistry:
    def __init__(self, packs: dict[str, CountryPack], default_code: str) -> None:
        if default_code not in packs:
            raise PackError(f"default pack {default_code!r} isn't enabled")
        self._packs = packs
        self.default_code = default_code

    def get(self, code: str) -> CountryPack | None:
        return self._packs.get(code)

    def require(self, code: str) -> CountryPack:
        pack = self._packs.get(code)
        if pack is None:
            raise PackError(f"pack {code!r} isn't enabled")
        return pack

    @property
    def codes(self) -> frozenset[str]:
        return frozenset(self._packs)

    @property
    def default(self) -> CountryPack:
        return self._packs[self.default_code]


def load_registry(
    directory: Path, enabled: list[str], default_code: str, *, production: bool
) -> PackRegistry:
    packs: dict[str, CountryPack] = {}
    for code in enabled:
        path = directory / code
        if not path.is_dir():
            raise PackError(f"pack folder {code!r} not found")
        pack = load_pack(path)
        if production and not pack.is_reviewed:
            raise PackError(
                f"{code} has status {pack.manifest.status.value} and can't run in production"
            )
        packs[code] = pack
        patterns = [(pack.identity.national_id_pattern, "[NATIONAL_ID]")]
        if pack.identity.phone_pattern:
            patterns.append((pack.identity.phone_pattern, "[PHONE]"))
        register_scrub_patterns(patterns)
    return PackRegistry(packs, default_code)
