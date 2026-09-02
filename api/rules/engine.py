"""Evaluation of the rule catalogue.

The engine is the only place that knows how rules combine. It decides nothing on
its own: every outcome it returns was produced by a rule and carries that rule's
id, message and evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from api.rules import registry
from api.rules.registry import GuardFn, RankingFn, RuleFn
from api.rules.types import (
    OUTCOME_PRECEDENCE,
    ApplicationSnapshot,
    Limits,
    Outcome,
    Ranked,
    RecordingSnapshot,
    RequiredField,
    UnitDecision,
    UnitSnapshot,
)

# Importing the rule modules is what registers them. Done here rather than in
# api/rules/__init__.py so that importing the registry alone stays cheap and
# free of cycles.
from api.rules import (  # noqa: F401  isort:skip
    asumisoikeus,
    lyhyt_korkotuki,
    tarveharkintainen,
    vapaarahoitteinen,
    yleiset,
)

#: An expired application short-circuits every apartment in the basket. The
#: engine has to name the rule that does it; the wording and the evidence still
#: come from the rule itself.
EXPIRY_RULE_ID = "YLEIS-VANHENTUNUT-01"


@dataclass(frozen=True, slots=True)
class FieldRequirement:
    """Why the application form is asking for something.

    The apartment is carried alongside the field so the form can say which
    chosen apartment made the section appear (SPEC section 2.4).
    """

    field: RequiredField
    unit_id: int
    unit_label: str
    rule_id: str
    rule_title_fi: str


def _worst(outcomes: Sequence[Outcome]) -> Outcome:
    """The most blocking outcome; ties broken by rule id so output is stable."""
    return min(outcomes, key=lambda o: (OUTCOME_PRECEDENCE.index(o.outcome), o.rule_id))


def decide_unit(snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits) -> UnitDecision:
    """Run every rule that applies to one apartment and combine the results."""
    applicable = registry.rules_for_form(unit.housing_form)

    recording = RecordingSnapshot.wrap(snapshot)
    outcomes: list[Outcome] = []
    guards: list[registry.RegisteredRule] = []

    for registered in applicable:
        if registered.meta.kind == "ranking_rule":
            continue  # ranking answers a different question; see rank_applicants
        if registered.meta.kind == "guard_rule":
            guards.append(registered)
            continue
        fn: RuleFn = registered.fn  # type: ignore[assignment]
        outcome = fn(recording, unit, limits)
        outcomes.append(outcome)
        if outcome.rule_id == EXPIRY_RULE_ID and outcome.outcome == "puuttuvat_tiedot":
            # Expired: nothing else about this application can be decided, and
            # the applicant gets one clear instruction instead of a wall of
            # unrelated results.
            return UnitDecision(
                unit_id=unit.id,
                outcome=outcome.outcome,
                deciding=outcome,
                all_outcomes=(outcome,),
            )

    consulted = recording._recorded_reads()
    for registered in guards:
        guard_fn: GuardFn = registered.fn  # type: ignore[assignment]
        outcomes.append(guard_fn(recording, unit, limits, consulted))

    if not outcomes:  # pragma: no cover - every form has at least the general rules
        raise ValueError(f"no rules registered for housing form {unit.housing_form}")

    deciding = _worst(outcomes)
    return UnitDecision(
        unit_id=unit.id,
        outcome=deciding.outcome,
        deciding=deciding,
        all_outcomes=tuple(outcomes),
    )


def decide(
    snapshot: ApplicationSnapshot, units: Sequence[UnitSnapshot], limits: Limits
) -> tuple[UnitDecision, ...]:
    return tuple(decide_unit(snapshot, unit, limits) for unit in units)


def rank_applicants(
    applicants: Sequence[ApplicationSnapshot], unit: UnitSnapshot, limits: Limits
) -> tuple[Ranked, ...]:
    """Order applicants for one apartment using the ranking rules of its form."""
    ranked: list[Ranked] = []
    for registered in registry.rules_for_form(unit.housing_form):
        if registered.meta.kind != "ranking_rule":
            continue
        fn: RankingFn = registered.fn  # type: ignore[assignment]
        ranked.extend(fn(applicants, unit, limits))
    return tuple(ranked)


def required_fields(
    units: Sequence[UnitSnapshot],
) -> Mapping[RequiredField, tuple[FieldRequirement, ...]]:
    """What the application form must ask for, given the apartments in the basket.

    The union of every applicable rule's ``requires``. The frontend renders this;
    it does not keep its own copy of the list.
    """
    found: dict[RequiredField, list[FieldRequirement]] = {}
    for unit in units:
        for registered in registry.rules_for_form(unit.housing_form):
            for field in registered.meta.requires:
                found.setdefault(field, []).append(
                    FieldRequirement(
                        field=field,
                        unit_id=unit.id,
                        unit_label=unit.label,
                        rule_id=registered.meta.id,
                        rule_title_fi=registered.meta.title_fi,
                    )
                )
    return {field: tuple(items) for field, items in sorted(found.items())}
