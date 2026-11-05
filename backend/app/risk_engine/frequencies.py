from dataclasses import dataclass
from fractions import Fraction

from app.risk_engine.types import Inheritance


@dataclass(frozen=True, slots=True)
class GeneInfo:
    gene: str
    inheritance: Inheritance
    carrier_frequency: Fraction
    detection_rate: Fraction
    conditions: tuple[str, ...] = ()
    # Genes where a change in either one can add up to the same condition, like HBA1 and HBA2.
    risk_group: str | None = None
    # Common conditions, like G6PD deficiency in men, that shouldn't reach the urgent queue.
    routine_when_hemizygous: bool = False


class GeneTable:
    """A country pack's gene data, handed in as values so the engine itself never touches a file."""

    def __init__(
        self, genes: dict[str, GeneInfo], panels: dict[str, frozenset[str]] | None = None
    ) -> None:
        self._genes = genes
        self._panels = panels or {}

    def get(self, gene: str) -> GeneInfo | None:
        return self._genes.get(gene)

    def panel(self, version: str) -> frozenset[str] | None:
        return self._panels.get(version)

    @property
    def genes(self) -> frozenset[str]:
        return frozenset(self._genes)
