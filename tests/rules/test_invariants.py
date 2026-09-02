"""The invariants that hold for every rule, present and future.

SPEC section 9 asks for a property test on the Outcome invariant. These are the
tests that a newly added rule has to pass without anyone remembering to write
them.
"""

from __future__ import annotations

import itertools
from typing import Any, get_args

import pytest

from api.rules.engine import decide_unit
from api.rules.registry import all_rules
from api.rules.types import Outcome, Ranked, RequiredField
from tests.conftest import LIMITS, application, unit

BLANK_VALUES = ["", "   "]
EMPTY_EVIDENCE: list[Any] = [{}, None]


@pytest.mark.parametrize(
    ("rule_id", "message_fi", "evidence"),
    [
        (rule_id, message, evidence)
        for rule_id, message, evidence in itertools.product(
            [*BLANK_VALUES, "OK-01"],
            [*BLANK_VALUES, "Selkeä suomenkielinen perustelu."],
            [*EMPTY_EVIDENCE, {"arvo": 1}],
        )
        # every combination except the one that is fully populated
        if not (rule_id.strip() and message.strip() and evidence)
    ],
)
def test_outcome_cannot_be_built_without_rule_message_and_evidence(
    rule_id: str, message_fi: str, evidence: Any
) -> None:
    with pytest.raises(ValueError):
        Outcome(outcome="kelpoinen", rule_id=rule_id, message_fi=message_fi, evidence=evidence)


def test_a_fully_populated_outcome_is_accepted_and_frozen() -> None:
    outcome = Outcome(
        outcome="kelpoinen",
        rule_id="OK-01",
        message_fi="Selkeä suomenkielinen perustelu.",
        evidence={"arvo": 1},
    )

    with pytest.raises(TypeError):
        outcome.evidence["arvo"] = 2  # type: ignore[index]


def test_unknown_outcome_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown outcome"):
        Outcome(
            outcome="maybe",  # type: ignore[arg-type]
            rule_id="OK-01",
            message_fi="Perustelu.",
            evidence={"arvo": 1},
        )


@pytest.mark.parametrize(
    ("rank", "rule_id", "message_fi", "evidence"),
    [
        (0, "OK-01", "Perustelu.", {"arvo": 1}),
        (1, " ", "Perustelu.", {"arvo": 1}),
        (1, "OK-01", " ", {"arvo": 1}),
        (1, "OK-01", "Perustelu.", {}),
    ],
)
def test_ranking_carries_the_same_obligation_as_an_outcome(
    rank: int, rule_id: str, message_fi: str, evidence: Any
) -> None:
    with pytest.raises(ValueError):
        Ranked(
            rank=rank,
            application_id=1,
            rule_id=rule_id,
            message_fi=message_fi,
            evidence=evidence,
        )


def test_every_rule_declares_documentable_metadata() -> None:
    """The catalogue is generated from this, so a rule without it is not shippable."""
    for registered in all_rules():
        meta = registered.meta
        assert meta.id.strip(), registered.fn
        assert meta.title_fi.strip(), meta.id
        assert meta.description_fi.strip(), meta.id
        assert meta.housing_forms, meta.id


def test_declared_required_fields_come_from_the_shared_vocabulary() -> None:
    """The frontend renders these keys; an unknown one would render nothing."""
    vocabulary = set(get_args(RequiredField))

    for registered in all_rules():
        assert set(registered.meta.requires) <= vocabulary, registered.meta.id


def test_declared_outcomes_match_what_the_rules_can_return() -> None:
    """Two rules promise never to refuse anyone. Hold them to it.

    A rule that widens its outcomes without updating its metadata would make the
    generated catalogue a lie, so the promise is checked rather than trusted.
    """
    promises = {
        registered.meta.id: set(registered.meta.outcomes)
        for registered in all_rules()
        if registered.meta.kind != "ranking_rule"
    }

    assert "ei_kelpoinen" not in promises["VAPAA-LUOTTO-01"]
    assert "ei_kelpoinen" not in promises["TARVE-TARVE-01"]
    assert "ei_kelpoinen" not in promises["YLEIS-VANHENTUNUT-01"]

    observed: dict[str, set[str]] = {}
    for form in ("vapaarahoitteinen", "lyhyt_korkotuki", "tarveharkintainen", "asumisoikeus"):
        for snapshot in _representative_applications():
            for outcome in decide_unit(snapshot, unit(housing_form=form), LIMITS).all_outcomes:
                observed.setdefault(outcome.rule_id, set()).add(outcome.outcome)

    for rule_id, seen in observed.items():
        assert seen <= promises[rule_id], rule_id


def _representative_applications() -> list[Any]:
    from tests.conftest import member

    return [
        application(),
        application(
            members=(member(income=None, assets=None, birth_year=None),),
            housing_need=None,
            order_number=None,
            deposit_acknowledged=None,
            credit_default_flag=None,
        ),
        application(
            members=(member(income=9000, assets=500000),),
            credit_default_flag=True,
            deposit_acknowledged=False,
            order_number="99",
        ),
    ]
