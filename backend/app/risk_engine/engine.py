from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import replace
from enum import Enum, auto
from fractions import Fraction

from app.risk_engine import rules
from app.risk_engine.frequencies import GeneInfo, GeneTable
from app.risk_engine.types import (
    DOMINANT,
    ON_THE_X,
    CoupleAssessment,
    CoupleFact,
    Finding,
    Flag,
    Inheritance,
    Label,
    PartnerRecord,
    Relationship,
    Reveal,
    RiskFact,
    Scenario,
    Sex,
    Viewer,
    Zygosity,
)

RULE_VERSION = "2026.11.1"

CITE_MENDELIAN = "Mendelian inheritance"
CITE_RESIDUAL = "Bayesian residual risk"
CITE_REVIEW = "Needs counsellor review"
CITE_BACKGROUND = "Wording set by clinical review"

BOTH = frozenset({Viewer.A, Viewer.B})


class _Copies(Enum):
    """What one person's findings in one gene add up to."""

    NONE = auto()
    UNCERTAIN = auto()
    ONE = auto()
    TWO = auto()
    HEMIZYGOUS = auto()
    INCONSISTENT = auto()


def _fact(
    scenario: Scenario,
    gene: str | None,
    label: Label,
    value: Fraction | None,
    citation: str,
    *flags: Flag,
) -> RiskFact:
    return RiskFact(
        id=f"{scenario.value}:{gene or '-'}:{label.value}",
        scenario=scenario,
        gene=gene,
        label=label,
        value=value,
        citation=citation,
        rule_version=RULE_VERSION,
        flags=frozenset(flags),
    )


def _by_gene(findings: Iterable[Finding]) -> dict[str, list[Finding]]:
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        if finding not in grouped[finding.gene]:
            grouped[finding.gene].append(finding)
    return grouped


def _copies(findings: list[Finding], inheritance: Inheritance, sex: Sex) -> _Copies:
    if not findings:
        return _Copies.NONE
    # A VUS in the gene means no number at all, even beside a pathogenic finding.
    if any(not finding.is_pathogenic for finding in findings):
        return _Copies.UNCERTAIN

    zygosities = {finding.zygosity for finding in findings}
    if inheritance in ON_THE_X:
        if sex is Sex.UNKNOWN:
            return _Copies.INCONSISTENT
        if sex is Sex.MALE:
            return (
                _Copies.HEMIZYGOUS if zygosities == {Zygosity.HEMIZYGOUS} else _Copies.INCONSISTENT
            )
        if Zygosity.HEMIZYGOUS in zygosities:
            return _Copies.INCONSISTENT
    elif Zygosity.HEMIZYGOUS in zygosities:
        return _Copies.INCONSISTENT

    if Zygosity.HOMOZYGOUS in zygosities or len(findings) > 1:
        # Two different variants may sit on the same copy or on opposite copies. Without phase
        # information the safe reading is the one that sends this person to a counsellor.
        return _Copies.TWO
    return _Copies.ONE


def _refer(gene: str, reason: Flag) -> RiskFact:
    return _fact(Scenario.REFER, gene, Label.REFER, None, CITE_REVIEW, reason)


def _possibly_affected(info: GeneInfo, copies: _Copies) -> RiskFact:
    routine = copies is _Copies.HEMIZYGOUS and info.routine_when_hemizygous
    flag = Flag.POSSIBLE_AFFECTED_ROUTINE if routine else Flag.POSSIBLE_AFFECTED
    return _fact(
        Scenario.POSSIBLE_AFFECTED, info.gene, Label.POSSIBLE_AFFECTED, None, CITE_REVIEW, flag
    )


def person_facts(findings: Iterable[Finding], sex: Sex, table: GeneTable) -> list[RiskFact]:
    """Facts about one person's own result. Holds nothing about any partner."""
    facts: list[RiskFact] = []
    for gene, gene_findings in sorted(_by_gene(findings).items()):
        info = table.get(gene)
        if info is None:
            facts.append(_refer(gene, Flag.UNKNOWN_GENE))
            continue
        copies = _copies(gene_findings, info.inheritance, sex)
        facts.extend(_person_gene_facts(info, copies, sex))
    return facts


def _person_gene_facts(
    info: GeneInfo, copies: _Copies, sex: Sex = Sex.UNKNOWN
) -> Iterator[RiskFact]:
    gene = info.gene
    if copies is _Copies.INCONSISTENT:
        yield _refer(gene, Flag.INCONSISTENT_DATA)
    elif copies is _Copies.UNCERTAIN:
        yield _fact(Scenario.UNCERTAIN_VUS, gene, Label.UNCERTAIN, None, CITE_REVIEW, Flag.VUS)
    elif info.inheritance in DOMINANT:
        yield from _dominant_facts(info, copies, sex)
    elif copies is _Copies.HEMIZYGOUS:
        yield _possibly_affected(info, copies)
    elif copies is _Copies.TWO:
        yield _possibly_affected(info, copies)
        if info.inheritance is Inheritance.X_LINKED:
            yield from _xl_mother_facts(Scenario.XL_TWO_COPIES_FEMALE, gene, rules.ONE)
    else:
        if info.inheritance is Inheritance.X_LINKED:
            yield from _xl_mother_facts(Scenario.XL_CARRIER_FEMALE, gene, rules.ONE_HALF)
        else:
            # No number: being a carrier is a state, and "100%" would only confuse.
            yield _fact(Scenario.CARRIER_SELF, gene, Label.CARRIER, None, CITE_MENDELIAN)


def _xl_mother_facts(scenario: Scenario, gene: str, passes_on: Fraction) -> Iterator[RiskFact]:
    yield _fact(scenario, gene, Label.SON_AFFECTED, passes_on, CITE_MENDELIAN, Flag.XL_FEMALE)
    yield _fact(scenario, gene, Label.DAUGHTER_CARRIER, passes_on, CITE_MENDELIAN, Flag.XL_FEMALE)


def _dominant_facts(info: GeneInfo, copies: _Copies, sex: Sex) -> Iterator[RiskFact]:
    """One changed copy is enough, so these are about passing it on, not about sharing it.

    The person themselves may be affected, which only a clinician can say, so the finding also
    goes to a person. Nothing here predicts that a child who inherits the change will be ill:
    how much a changed copy does varies, and that is the clinician's conversation too.
    """
    gene = info.gene
    yield _possibly_affected(info, copies)
    everyone = copies in (_Copies.TWO, _Copies.HEMIZYGOUS)
    if info.inheritance is Inheritance.AUTOSOMAL_DOMINANT:
        passes_on = rules.ONE if everyone else rules.ONE_HALF
        yield _fact(Scenario.AD_SELF, gene, Label.INHERITS_CHANGE, passes_on, CITE_MENDELIAN)
        if passes_on != rules.ONE:
            yield _fact(
                Scenario.AD_SELF, gene, Label.DOES_NOT_INHERIT, 1 - passes_on, CITE_MENDELIAN
            )
        return
    # X-linked dominant. A father passes his only X to every daughter and to no son, which is the
    # one pattern a square drawn for the mother cannot show.
    if copies is _Copies.HEMIZYGOUS:
        son, daughter = rules.ZERO, rules.ONE
    else:
        son = daughter = rules.ONE if everyone else rules.ONE_HALF
    yield _fact(Scenario.XLD_SELF, gene, Label.SON_INHERITS, son, CITE_MENDELIAN, Flag.XL_FEMALE)
    yield _fact(
        Scenario.XLD_SELF, gene, Label.DAUGHTER_INHERITS, daughter, CITE_MENDELIAN, Flag.XL_FEMALE
    )


def _passes_on(copies: _Copies) -> Fraction:
    return rules.ONE if copies in (_Copies.TWO, _Copies.HEMIZYGOUS) else rules.ONE_HALF


def couple_assessment(
    a: PartnerRecord, b: PartnerRecord, relationship: Relationship, table: GeneTable
) -> CoupleAssessment:
    a_genes, b_genes = _by_gene(a.findings), _by_gene(b.findings)
    facts: list[CoupleFact] = []
    shared: set[str] = set()

    grouped_review = _risk_group_overlaps(a_genes, b_genes, table)
    if grouped_review:
        facts.append(
            CoupleFact(
                _fact(
                    Scenario.COUPLE_REVIEW,
                    None,
                    Label.REVIEW,
                    None,
                    CITE_REVIEW,
                    Flag.REVIEW_NEEDED,
                ),
                BOTH,
            )
        )

    review_needed = bool(grouped_review)
    for gene in sorted(a_genes.keys() | b_genes.keys()):
        if gene in grouped_review:
            continue
        info = table.get(gene)
        from_a, from_b = a_genes.get(gene, []), b_genes.get(gene, [])
        if info is None:
            facts.extend(_holder_facts(_refer(gene, Flag.UNKNOWN_GENE), from_a, from_b))
            if from_a and from_b:
                shared.add(gene)
            continue

        a_copies = _copies(from_a, info.inheritance, a.sex)
        b_copies = _copies(from_b, info.inheritance, b.sex)
        unusable = (_Copies.UNCERTAIN, _Copies.INCONSISTENT)
        if from_a and from_b and (a_copies in unusable or b_copies in unusable):
            # Both have something here, and it can't be reduced to a number. Showing either
            # partner a figure would ignore the other's unresolved finding.
            review_needed = True
            facts.append(
                CoupleFact(
                    _fact(
                        Scenario.COUPLE_REVIEW,
                        gene,
                        Label.REVIEW,
                        None,
                        CITE_REVIEW,
                        Flag.REVIEW_NEEDED,
                        *_vus_flag(a_copies, b_copies),
                    ),
                    BOTH,
                )
            )
            continue
        if a_copies in unusable or b_copies in unusable:
            facts.extend(
                _visible_to(
                    Viewer.A if from_a else Viewer.B,
                    _person_gene_facts(
                        info,
                        a_copies if from_a else b_copies,
                        a.sex if from_a else b.sex,
                    ),
                )
            )
            continue

        if info.inheritance in DOMINANT:
            # One changed copy is enough, so the chance comes from the parent who has it, not from
            # the two of them together. There is nothing to combine, and a shared-finding figure
            # would be the wrong arithmetic as well as the wrong story.
            if from_a and from_b:
                review_needed = True
                facts.append(
                    CoupleFact(
                        _fact(
                            Scenario.COUPLE_REVIEW,
                            gene,
                            Label.REVIEW,
                            None,
                            CITE_REVIEW,
                            Flag.REVIEW_NEEDED,
                        ),
                        BOTH,
                    )
                )
                continue
            holder = Viewer.A if from_a else Viewer.B
            facts.extend(
                _visible_to(
                    holder,
                    _person_gene_facts(
                        info,
                        a_copies if from_a else b_copies,
                        a.sex if from_a else b.sex,
                    ),
                )
            )
            continue

        if info.inheritance is Inheritance.X_LINKED:
            xl_facts, is_shared = _x_linked(info, a, b, a_copies, b_copies)
            facts.extend(xl_facts)
            if is_shared:
                shared.add(gene)
        elif from_a and from_b:
            shared.add(gene)
            facts.extend(_shared_recessive(gene, a_copies, b_copies))
        else:
            holder_copies = a_copies if from_a else b_copies
            other = b if from_a else a
            facts.append(
                CoupleFact(
                    _one_carrier(info, holder_copies, other, relationship),
                    frozenset({Viewer.A if from_a else Viewer.B}),
                )
            )

    if rules.KINSHIP[relationship] > 0 and not shared and not review_needed:
        facts.append(
            CoupleFact(
                # Deliberately no figure. Published estimates describe unscreened couples, so they
                # can't be quoted as what remains after a negative panel. See issue H4.
                _fact(
                    Scenario.CONSANGUINITY_BACKGROUND,
                    None,
                    Label.BACKGROUND,
                    None,
                    CITE_BACKGROUND,
                    Flag.CONSANGUINEOUS,
                ),
                BOTH,
            )
        )
    return CoupleAssessment(
        facts=tuple(facts), shared_genes=frozenset(shared), review_needed=review_needed
    )


def _vus_flag(*copies: _Copies) -> tuple[Flag, ...]:
    return (Flag.VUS,) if _Copies.UNCERTAIN in copies else ()


def _risk_group_overlaps(
    a_genes: dict[str, list[Finding]], b_genes: dict[str, list[Finding]], table: GeneTable
) -> set[str]:
    """Genes where the partners hold different members of one risk group, such as HBA1 and HBA2."""

    def pathogenic_by_group(genes: dict[str, list[Finding]]) -> dict[str, set[str]]:
        groups: dict[str, set[str]] = defaultdict(set)
        for gene, findings in genes.items():
            info = table.get(gene)
            if info and info.risk_group and any(f.is_pathogenic for f in findings):
                groups[info.risk_group].add(gene)
        return groups

    a_groups, b_groups = pathogenic_by_group(a_genes), pathogenic_by_group(b_genes)
    overlaps: set[str] = set()
    for group in a_groups.keys() & b_groups.keys():
        combined = a_groups[group] | b_groups[group]
        if len(combined) > 1:
            overlaps |= combined
    return overlaps


def _holder_facts(
    fact: RiskFact, from_a: list[Finding], from_b: list[Finding]
) -> Iterator[CoupleFact]:
    holders = frozenset(viewer for viewer, held in ((Viewer.A, from_a), (Viewer.B, from_b)) if held)
    yield CoupleFact(fact, holders)


def _visible_to(viewer: Viewer, facts: Iterable[RiskFact]) -> Iterator[CoupleFact]:
    for fact in facts:
        yield CoupleFact(fact, frozenset({viewer}))


def _shared_recessive(gene: str, a: _Copies, b: _Copies) -> Iterator[CoupleFact]:
    two, carrier, neither = rules.child_outcomes(_passes_on(a), _passes_on(b))
    outcomes = ((Label.TWO_COPIES, two), (Label.CARRIER, carrier), (Label.NEITHER, neither))
    for label, value in outcomes:
        yield CoupleFact(
            _fact(Scenario.COUPLE_SHARED_AR, gene, label, value, CITE_MENDELIAN, Flag.SHARED_AR),
            BOTH,
        )


def _one_carrier(
    info: GeneInfo, holder: _Copies, other: PartnerRecord, relationship: Relationship
) -> RiskFact:
    prior = rules.carrier_prior(info.carrier_frequency, relationship)
    if other.tested_genes is not None and info.gene in other.tested_genes:
        partner_is_carrier = rules.residual_after_negative(prior, info.detection_rate)
        scenario, citation = Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE, CITE_RESIDUAL
    else:
        partner_is_carrier = prior
        scenario, citation = Scenario.COUPLE_ONE_CARRIER_UNTESTED, CITE_RESIDUAL
    two_copies, _, _ = rules.child_outcomes(_passes_on(holder), partner_is_carrier * rules.ONE_HALF)
    return _fact(scenario, info.gene, Label.TWO_COPIES, two_copies, citation)


def _x_linked(
    info: GeneInfo, a: PartnerRecord, b: PartnerRecord, a_copies: _Copies, b_copies: _Copies
) -> tuple[list[CoupleFact], bool]:
    if {a.sex, b.sex} != {Sex.FEMALE, Sex.MALE}:
        holders = []
        if a_copies is not _Copies.NONE:
            holders.append(Viewer.A)
        if b_copies is not _Copies.NONE:
            holders.append(Viewer.B)
        return [CoupleFact(_refer(info.gene, Flag.INCONSISTENT_DATA), frozenset(holders))], len(
            holders
        ) == 2

    a_is_mother = a.sex is Sex.FEMALE
    mother_copies, father_copies = (a_copies, b_copies) if a_is_mother else (b_copies, a_copies)
    mother, father = (Viewer.A, Viewer.B) if a_is_mother else (Viewer.B, Viewer.A)
    gene = info.gene

    if mother_copies is not _Copies.NONE and father_copies is not _Copies.NONE:
        passes_on = _passes_on(mother_copies)
        two, carrier, neither = rules.child_outcomes(passes_on, rules.ONE)
        scenario = Scenario.COUPLE_XL
        facts = [
            _fact(scenario, gene, Label.SON_AFFECTED, passes_on, CITE_MENDELIAN, Flag.XL_COUPLE),
            _fact(scenario, gene, Label.DAUGHTER_TWO_COPIES, two, CITE_MENDELIAN, Flag.XL_COUPLE),
            _fact(scenario, gene, Label.DAUGHTER_CARRIER, carrier, CITE_MENDELIAN, Flag.XL_COUPLE),
            _fact(scenario, gene, Label.DAUGHTER_NEITHER, neither, CITE_MENDELIAN, Flag.XL_COUPLE),
        ]
        return [CoupleFact(fact, BOTH) for fact in facts], True

    if mother_copies is not _Copies.NONE:
        return list(_visible_to(mother, _person_gene_facts(info, mother_copies, Sex.FEMALE))), False

    return [
        CoupleFact(fact, frozenset({father}))
        for fact in (
            _fact(Scenario.XL_FATHER, gene, Label.DAUGHTER_CARRIER, rules.ONE, CITE_MENDELIAN),
            _fact(Scenario.XL_FATHER, gene, Label.SON_AFFECTED, rules.ZERO, CITE_MENDELIAN),
        )
    ], False


def partner_view(assessment: CoupleAssessment, viewer: Viewer, reveal: Reveal) -> list[RiskFact]:
    """The only way couple facts leave the engine.

    A partner's findings stay out unless they're shared. At the "yes or no" level, gene names go
    too, along with anything else that could point at which gene it was, including this person's
    own residual figures, since seeing which genes have one would show which gene doesn't.
    """
    visible = [item for item in assessment.facts if viewer in item.visible_to]
    if reveal is Reveal.GENES:
        return [item.fact for item in visible]

    anonymous: list[RiskFact] = []
    shared_number: dict[str, int] = {}
    for item in visible:
        if item.visible_to != BOTH:
            continue
        gene = item.fact.gene
        if gene is None:
            anonymous.append(item.fact)
            continue
        number = shared_number.setdefault(gene, len(shared_number) + 1)
        anonymous.append(
            replace(
                item.fact,
                gene=None,
                id=f"{item.fact.scenario.value}:shared-{number}:{item.fact.label.value}",
            )
        )
    return anonymous
