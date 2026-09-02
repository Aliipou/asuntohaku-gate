"""How rules combine: precedence, the expiry short-circuit, and the adaptive form."""

from __future__ import annotations

import datetime as dt

from api.rules.engine import decide, decide_unit, rank_applicants, required_fields
from tests.conftest import LIMITS, NOW, application, member, unit

VAPAA = unit(id=10, label="Kotikatu 3 A 12", housing_form="vapaarahoitteinen", rent=900)
TARVE = unit(id=20, label="Purolantie 8 B 3", housing_form="tarveharkintainen", rent=780)
LYHYT = unit(id=30, label="Ratakuja 5 C 21", housing_form="lyhyt_korkotuki", rent=820)
ASO = unit(id=40, label="Niittypolku 2 A 6", housing_form="asumisoikeus", rent=760)


def test_a_blocking_rule_decides_the_row() -> None:
    """One apartment, several rules: the row shows the most blocking outcome.

    Here the income rule refuses and the wealth rule cannot decide. The row is a
    refusal, and it names the rule that refused rather than the one that was
    merely incomplete.
    """
    snapshot = application(members=(member(income=6000, assets=None),), housing_need="ahtaasti")

    decision = decide_unit(snapshot, TARVE, LIMITS)

    assert decision.outcome == "ei_kelpoinen"
    assert decision.deciding.rule_id == "TARVE-TULO-01"
    assert {o.outcome for o in decision.all_outcomes} >= {"ei_kelpoinen", "puuttuvat_tiedot"}


def test_missing_information_never_becomes_a_rejection() -> None:
    """An application that has told us nothing yet is undecidable, not refused."""
    snapshot = application(
        members=(member(income=None, assets=None, birth_year=None),),
        housing_need=None,
        order_number=None,
        deposit_acknowledged=None,
        credit_default_flag=None,
    )

    decisions = decide(snapshot, [VAPAA, TARVE, LYHYT, ASO], LIMITS)

    assert {d.outcome for d in decisions} == {"puuttuvat_tiedot"}


def test_one_basket_can_hold_different_outcomes() -> None:
    """Scenario 3: over the needs-assessed income limit, still fine for open stock."""
    snapshot = application(members=(member(income=3500, assets=1000),))

    by_unit = {d.unit_id: d for d in decide(snapshot, [VAPAA, TARVE], LIMITS)}

    assert by_unit[VAPAA.id].outcome == "kelpoinen"
    assert by_unit[TARVE.id].outcome == "ei_kelpoinen"
    assert by_unit[TARVE.id].deciding.rule_id == "TARVE-TULO-01"


def test_expiry_short_circuits_every_apartment() -> None:
    """Scenario 8: an expired application resets all of its decisions."""
    created = NOW - dt.timedelta(days=122)
    snapshot = application(created_at=created, expires_at=created + dt.timedelta(days=92))

    decisions = decide(snapshot, [VAPAA, TARVE, ASO], LIMITS)

    assert {d.outcome for d in decisions} == {"puuttuvat_tiedot"}
    for decision in decisions:
        assert decision.deciding.rule_id == "YLEIS-VANHENTUNUT-01"
        assert len(decision.all_outcomes) == 1


def test_every_decision_carries_a_rule_a_message_and_evidence() -> None:
    """SPEC section 2.1, over every housing form the engine can be asked about."""
    snapshot = application()

    for decision in decide(snapshot, [VAPAA, TARVE, LYHYT, ASO], LIMITS):
        for outcome in decision.all_outcomes:
            assert outcome.rule_id
            assert outcome.message_fi.strip()
            assert outcome.evidence


def test_the_form_grows_when_a_needs_assessed_apartment_is_added() -> None:
    """Scenario 2, from the engine's side: which fields the basket now needs."""
    before = required_fields([VAPAA])
    after = required_fields([VAPAA, TARVE])

    assert "assets" not in before
    assert "housing_need" not in before
    assert "assets" in after
    assert "housing_need" in after
    assert set(before) < set(after)


def test_a_new_field_names_the_apartment_that_caused_it() -> None:
    """SPEC section 2.4: the form has to say which chosen apartment requires this."""
    fields = required_fields([VAPAA, TARVE])

    causes = fields["housing_need"]
    assert {c.unit_id for c in causes} == {TARVE.id}
    assert {c.unit_label for c in causes} == {"Purolantie 8 B 3"}
    assert all(c.rule_id.startswith("TARVE-") for c in causes)
    assert all(c.rule_title_fi for c in causes)


def test_removing_the_apartment_removes_the_field_again() -> None:
    assert set(required_fields([VAPAA, TARVE])) - set(required_fields([VAPAA])) == {
        "assets",
        "housing_need",
    }


def test_short_term_stock_does_not_make_the_form_ask_about_wealth() -> None:
    fields = required_fields([LYHYT])

    assert set(fields) == {"household_income", "household_size"}


def test_ranking_runs_only_for_forms_that_rank() -> None:
    applicants = [
        application(id=1, order_number="000900"),
        application(id=2, order_number="000100"),
    ]

    assert [r.application_id for r in rank_applicants(applicants, ASO, LIMITS)] == [2, 1]
    assert rank_applicants(applicants, VAPAA, LIMITS) == ()
    assert [r.rule_id for r in rank_applicants(applicants, TARVE, LIMITS)] == [
        "TARVE-SIJOITUS-01",
        "TARVE-SIJOITUS-01",
    ]
