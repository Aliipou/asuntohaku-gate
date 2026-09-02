"""LYHYT-TULO-01 and the guard rule LYHYT-EI-VARALLISUUS-01."""

from __future__ import annotations

import pytest

from api.rules.engine import decide_unit
from api.rules.lyhyt_korkotuki import (
    FORBIDDEN_FIELDS,
    income_within_limit,
    no_wealth_or_need_consulted,
)
from tests.conftest import LIMITS, application, member, unit

LYHYT = "lyhyt_korkotuki"

# Limits in play: 3 800 €/kk for one person in the capital region, 3 400 €/kk
# elsewhere, 8 400 €/kk for four people in the capital region, plus 1 100 € for
# each person beyond that.
TULO_CASES = [
    # id, incomes, city, expected
    ("yhden hengen tulot rajan alle", [3000], "Helsinki", "kelpoinen"),
    ("yhden hengen tulot rajan yli", [4000], "Helsinki", "ei_kelpoinen"),
    ("tulot puuttuvat", [None], "Helsinki", "puuttuvat_tiedot"),
    ("tulot täsmälleen rajalla", [3800], "Helsinki", "kelpoinen"),
    ("euron rajan yli", [3801], "Helsinki", "ei_kelpoinen"),
    ("pääkaupunkiseudun ulkopuolella raja on matalampi", [3600], "Tampere", "ei_kelpoinen"),
    ("sama tulo pääkaupunkiseudulla mahtuu rajaan", [3600], "Helsinki", "kelpoinen"),
]


@pytest.mark.parametrize(
    ("incomes", "city", "expected"),
    [(c[1], c[2], c[3]) for c in TULO_CASES],
    ids=[c[0] for c in TULO_CASES],
)
def test_income_within_limit(incomes: list[int | None], city: str, expected: str) -> None:
    snapshot = application(members=tuple(member(income=i) for i in incomes))
    outcome = income_within_limit(snapshot, unit(housing_form=LYHYT, city=city), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "LYHYT-TULO-01"
    assert outcome.evidence["tuloraja_eur_kk"]


def test_limit_grows_beyond_the_tabulated_household_sizes() -> None:
    """A five-person household is past the table, so the per-person extension applies.

    Capital region: 8 400 € for four, plus 1 100 € for the fifth person.
    """
    five = tuple(member(role="muu", income=1900) for _ in range(5))
    outcome = income_within_limit(
        application(members=five), unit(housing_form=LYHYT, city="Helsinki"), LIMITS
    )

    assert outcome.evidence["tuloraja_eur_kk"] == 9500
    assert outcome.evidence["ruokakunnan_koko"] == 5
    assert outcome.outcome == "kelpoinen"


GUARD_CASES = [
    ("mitään ei luettu", frozenset(), "kelpoinen"),
    ("vain sallittuja kenttiä luettu", frozenset({"members", "total_monthly_income"}), "kelpoinen"),
    ("varallisuus luettu", frozenset({"total_assets"}), "ei_kelpoinen"),
    ("jäsenen varallisuus luettu", frozenset({"assets_eur"}), "ei_kelpoinen"),
    ("asunnontarve luettu", frozenset({"housing_need"}), "ei_kelpoinen"),
]


@pytest.mark.parametrize(
    ("consulted", "expected"),
    [(c[1], c[2]) for c in GUARD_CASES],
    ids=[c[0] for c in GUARD_CASES],
)
def test_guard_rule(consulted: frozenset[str], expected: str) -> None:
    outcome = no_wealth_or_need_consulted(
        application(), unit(housing_form=LYHYT), LIMITS, consulted
    )

    assert outcome.outcome == expected
    assert outcome.rule_id == "LYHYT-EI-VARALLISUUS-01"


def test_deciding_a_short_term_unit_consults_no_wealth_or_need_data() -> None:
    """The regression this guard exists for, run end to end through the engine.

    If a rule for this housing form ever starts reading wealth or housing-need
    data, the recorded field set changes and this fails.
    """
    decision = decide_unit(application(), unit(housing_form=LYHYT), LIMITS)

    guard = next(o for o in decision.all_outcomes if o.rule_id == "LYHYT-EI-VARALLISUUS-01")
    assert guard.outcome == "kelpoinen"
    assert guard.evidence["kielletyt_luetut_kentat"] == []
    assert not set(guard.evidence["luetut_kentat"]) & FORBIDDEN_FIELDS


def test_guard_catches_wealth_read_through_a_household_member() -> None:
    """Reaching wealth via snapshot.members[0].assets_eur must be recorded too."""
    from api.rules.types import RecordingSnapshot

    recording = RecordingSnapshot.wrap(application())
    _ = recording.members[0].assets_eur

    outcome = no_wealth_or_need_consulted(
        recording, unit(housing_form=LYHYT), LIMITS, recording._recorded_reads()
    )

    assert outcome.outcome == "ei_kelpoinen"
    assert "assets_eur" in outcome.evidence["kielletyt_luetut_kentat"]
    assert "varallisuus" in outcome.message_fi
