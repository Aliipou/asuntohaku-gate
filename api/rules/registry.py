"""The rule registry.

Rules declare their metadata at the point of definition. That metadata is the
single source for three things: which rules run for an apartment, which form
fields the application has to ask for, and the generated rule catalogue in
``docs/saannot.md``. Nothing derived from it is written by hand anywhere else.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from api.rules.types import (
    ApplicationSnapshot,
    Limits,
    Outcome,
    OutcomeValue,
    Ranked,
    RequiredField,
    RuleMeta,
    UnitSnapshot,
)

#: Housing forms a rule can be declared for, plus the marker for a rule that
#: applies to every form.
ALL_FORMS = "*"

type RuleFn = Callable[[ApplicationSnapshot, UnitSnapshot, Limits], Outcome]
type RankingFn = Callable[[Sequence[ApplicationSnapshot], UnitSnapshot, Limits], Sequence[Ranked]]
type GuardFn = Callable[[ApplicationSnapshot, UnitSnapshot, Limits, frozenset[str]], Outcome]


@dataclass(frozen=True, slots=True)
class RegisteredRule:
    meta: RuleMeta
    fn: RuleFn | RankingFn | GuardFn


_REGISTRY: dict[str, RegisteredRule] = {}


class DuplicateRuleError(ValueError):
    pass


def _register(meta: RuleMeta, fn: RuleFn | RankingFn | GuardFn) -> None:
    if meta.id in _REGISTRY:
        raise DuplicateRuleError(f"rule {meta.id} is already registered")
    _REGISTRY[meta.id] = RegisteredRule(meta=meta, fn=fn)


def _meta(
    kind: Literal["rule", "ranking_rule", "guard_rule"],
    rule_id: str,
    housing_forms: Sequence[str],
    requires: Sequence[RequiredField],
    title_fi: str,
    description_fi: str,
    outcomes: Sequence[OutcomeValue],
) -> RuleMeta:
    return RuleMeta(
        id=rule_id,
        kind=kind,
        housing_forms=tuple(housing_forms),
        requires=tuple(requires),
        title_fi=title_fi,
        description_fi=description_fi,
        outcomes=tuple(outcomes),
    )


def rule(
    *,
    id: str,
    housing_forms: Sequence[str],
    requires: Sequence[RequiredField],
    title_fi: str,
    description_fi: str,
    outcomes: Sequence[OutcomeValue] = ("kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen"),
) -> Callable[[RuleFn], RuleFn]:
    """An eligibility rule: one application, one apartment, one outcome."""

    def decorate(fn: RuleFn) -> RuleFn:
        _register(
            _meta("rule", id, housing_forms, requires, title_fi, description_fi, outcomes), fn
        )
        return fn

    return decorate


def ranking_rule(
    *,
    id: str,
    housing_forms: Sequence[str],
    requires: Sequence[RequiredField],
    title_fi: str,
    description_fi: str,
) -> Callable[[RankingFn], RankingFn]:
    """A ranking rule: several applicants for one apartment, put in order.

    Ranking answers a comparative question, so it cannot be expressed as a rule
    from a single application to a pass or a fail. It is a separate kind rather
    than an ``Outcome`` with an ordinal smuggled into the evidence.
    """

    def decorate(fn: RankingFn) -> RankingFn:
        _register(
            _meta("ranking_rule", id, housing_forms, requires, title_fi, description_fi, ()), fn
        )
        return fn

    return decorate


def guard_rule(
    *,
    id: str,
    housing_forms: Sequence[str],
    requires: Sequence[RequiredField],
    title_fi: str,
    description_fi: str,
    outcomes: Sequence[OutcomeValue] = ("kelpoinen", "ei_kelpoinen"),
) -> Callable[[GuardFn], GuardFn]:
    """A guard rule, which additionally receives the set of fields that were read.

    Used to hold a regression shut: see LYHYT-EI-VARALLISUUS-01.
    """

    def decorate(fn: GuardFn) -> GuardFn:
        _register(
            _meta("guard_rule", id, housing_forms, requires, title_fi, description_fi, outcomes),
            fn,
        )
        return fn

    return decorate


def all_rules() -> tuple[RegisteredRule, ...]:
    """Every registered rule, ordered by id so output is reproducible."""
    return tuple(sorted(_REGISTRY.values(), key=lambda r: r.meta.id))


def get_rule(rule_id: str) -> RegisteredRule:
    return _REGISTRY[rule_id]


def rules_for_form(housing_form: str) -> tuple[RegisteredRule, ...]:
    """Rules that apply to a housing form, including the cross-cutting ones."""
    return tuple(
        r
        for r in all_rules()
        if housing_form in r.meta.housing_forms or ALL_FORMS in r.meta.housing_forms
    )
