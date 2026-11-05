from fractions import Fraction

from app.risk_engine.types import Relationship

ONE_HALF = Fraction(1, 2)
ONE = Fraction(1)
ZERO = Fraction(0)

# Coefficient of relationship: the chance a relative carries the same allele by shared descent.
KINSHIP: dict[Relationship, Fraction] = {
    Relationship.DOUBLE_FIRST_COUSINS: Fraction(1, 4),
    Relationship.FIRST_COUSINS: Fraction(1, 8),
    Relationship.FIRST_COUSINS_ONCE_REMOVED: Fraction(1, 16),
    Relationship.SECOND_COUSINS: Fraction(1, 32),
    Relationship.UNRELATED: ZERO,
    Relationship.UNKNOWN: ZERO,
}


def carrier_prior(carrier_frequency: Fraction, relationship: Relationship) -> Fraction:
    """Chance a partner carries the allele, given that the other partner is known to."""
    r = KINSHIP[relationship]
    return r + (1 - r) * carrier_frequency


def residual_after_negative(prior: Fraction, detection_rate: Fraction) -> Fraction:
    """Bayes: the chance of still being a carrier after testing negative.

    The prior has to be the kinship-adjusted one. Using the population frequency here understates
    the risk for a related couple.
    """
    if not (0 <= prior < 1 and 0 <= detection_rate <= 1):
        raise ValueError("prior must be in [0, 1) and detection rate in [0, 1]")
    return prior * (1 - detection_rate) / (1 - prior * detection_rate)


def child_outcomes(from_a: Fraction, from_b: Fraction) -> tuple[Fraction, Fraction, Fraction]:
    """Two copies, one copy and no copies, from each parent's chance of passing a change on.

    Carrier, homozygous, compound and tested-negative parents all reduce to that one number, so
    every combination comes from this one calculation.
    """
    two_copies = from_a * from_b
    neither = (1 - from_a) * (1 - from_b)
    return two_copies, 1 - two_copies - neither, neither
