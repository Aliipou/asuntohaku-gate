"""Each demo scenario must land on the rule SPEC section 8 says it demonstrates.

Without this, a rule change can quietly turn scenario 6 into a rent refusal and
the demo still runs — it just stops showing what it was built to show. That
happened once while these were being written, which is why the test exists.
"""

from __future__ import annotations

import datetime as dt

import pytest

from api.rules.engine import decide, required_fields
from seeds.limits import DEMO_LIMITS
from seeds.scenarios import Scenario, scenarios

NOW = dt.datetime(2026, 9, 2, 12, 0, tzinfo=dt.UTC)
SCENARIOS = scenarios(NOW)

#: number -> (unit index, expected outcome). The apartment each scenario is about.
EXPECTED = {
    1: (0, "kelpoinen"),
    2: (1, "puuttuvat_tiedot"),
    3: (1, "ei_kelpoinen"),
    4: (0, "kelpoinen"),
    5: (0, "puuttuvat_tiedot"),
    6: (0, "puuttuvat_tiedot"),
    7: (0, "ei_kelpoinen"),
    8: (0, "puuttuvat_tiedot"),
}


def _decisions(scenario: Scenario) -> tuple:
    return decide(scenario.application, scenario.units, DEMO_LIMITS)


def test_there_are_eight_scenarios_each_on_a_different_rule() -> None:
    assert len(SCENARIOS) == 8
    assert [s.number for s in SCENARIOS] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert len({s.demonstrates for s in SCENARIOS}) == 8


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: f"{s.number}-{s.demonstrates}")
def test_scenario_lands_on_the_rule_it_demonstrates(scenario: Scenario) -> None:
    index, expected_outcome = EXPECTED[scenario.number]
    decision = _decisions(scenario)[index]

    assert decision.outcome == expected_outcome
    assert scenario.demonstrates in {o.rule_id for o in decision.all_outcomes}


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: str(s.number))
def test_every_scenario_outcome_is_fully_explained(scenario: Scenario) -> None:
    for decision in _decisions(scenario):
        for outcome in decision.all_outcomes:
            assert outcome.rule_id
            assert outcome.message_fi.strip()
            assert outcome.evidence


def test_scenario_2_grows_the_form_and_names_the_apartment_that_did_it() -> None:
    """Scenario 2 is the adaptive-form demonstration; it has to actually adapt."""
    one, two = SCENARIOS[0], SCENARIOS[1]

    before, after = required_fields(one.units), required_fields(two.units)
    new_fields = set(after) - set(before)

    assert new_fields == {"assets", "housing_need"}
    causing = {c.unit_label for field in new_fields for c in after[field]}
    assert causing == {two.units[1].label}


def test_scenario_2_is_a_mixed_result_for_the_same_applicant() -> None:
    two = SCENARIOS[1]
    outcomes = [d.outcome for d in _decisions(two)]

    assert outcomes == ["kelpoinen", "puuttuvat_tiedot"]
    assert two.application is SCENARIOS[0].application


def test_scenario_4_splits_on_the_age_exemption_alone() -> None:
    """Same household, same wealth, two apartments, opposite outcomes."""
    aso, needs = _decisions(SCENARIOS[3])

    assert aso.outcome == "kelpoinen"
    exemption = next(o for o in aso.all_outcomes if o.rule_id == "ASO-VARALLISUUS-01")
    assert exemption.evidence["poikkeus"] == "ikapoikkeus"

    assert needs.outcome == "ei_kelpoinen"
    assert needs.deciding.rule_id == "TARVE-VARALLISUUS-01"


def test_scenario_6_is_not_a_rejection() -> None:
    """A credit default marker asks for context. It must not refuse anyone."""
    decision = _decisions(SCENARIOS[5])[0]

    assert decision.outcome == "puuttuvat_tiedot"
    assert decision.deciding.rule_id == "VAPAA-LUOTTO-01"
    assert all(o.outcome != "ei_kelpoinen" for o in decision.all_outcomes)


def test_scenario_8_resets_every_apartment_in_the_basket() -> None:
    decisions = _decisions(SCENARIOS[7])

    assert len(decisions) == 2
    for decision in decisions:
        assert decision.outcome == "puuttuvat_tiedot"
        assert decision.deciding.rule_id == "YLEIS-VANHENTUNUT-01"
        assert len(decision.all_outcomes) == 1


def test_expiry_is_three_calendar_months_not_ninety_days() -> None:
    """31 January plus three months is 30 April, and the clamp is tested here."""
    from api.app.dates import add_months

    assert add_months(dt.datetime(2026, 1, 31, tzinfo=dt.UTC), 3) == dt.datetime(
        2026, 4, 30, tzinfo=dt.UTC
    )
    assert add_months(dt.datetime(2026, 11, 30, tzinfo=dt.UTC), 3) == dt.datetime(
        2027, 2, 28, tzinfo=dt.UTC
    )
