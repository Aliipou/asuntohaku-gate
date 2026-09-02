"""TARVE-TULO-01, TARVE-VARALLISUUS-01, TARVE-TARVE-01, TARVE-SIJOITUS-01."""

from __future__ import annotations

import datetime as dt

import pytest

from api.rules.tarveharkintainen import (
    assets_within_limit,
    housing_need_stated,
    income_within_limit,
    needs_ranking,
)
from tests.conftest import LIMITS, NOW, application, member, unit

TARVE = "tarveharkintainen"

# Limits in play: 3 100 €/kk income for one person in the capital region,
# 42 000 € household assets.
TULO_CASES = [
    ("tulot rajan alle", [2500], "Helsinki", "kelpoinen"),
    ("tulot rajan yli", [3500], "Helsinki", "ei_kelpoinen"),
    ("tulot puuttuvat", [None], "Helsinki", "puuttuvat_tiedot"),
    ("tulot täsmälleen rajalla", [3100], "Helsinki", "kelpoinen"),
    ("euron rajan yli", [3101], "Helsinki", "ei_kelpoinen"),
    ("raja on tiukempi kuin lyhyessä korkotuessa", [3500], "Tampere", "ei_kelpoinen"),
]


@pytest.mark.parametrize(
    ("incomes", "city", "expected"),
    [(c[1], c[2], c[3]) for c in TULO_CASES],
    ids=[c[0] for c in TULO_CASES],
)
def test_income_within_limit(incomes: list[int | None], city: str, expected: str) -> None:
    snapshot = application(members=tuple(member(income=i) for i in incomes))
    outcome = income_within_limit(snapshot, unit(housing_form=TARVE, city=city), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "TARVE-TULO-01"


VARALLISUUS_CASES = [
    ("varallisuus rajan alle", [10000], "kelpoinen"),
    ("varallisuus rajan yli", [60000], "ei_kelpoinen"),
    ("varallisuus puuttuu", [None], "puuttuvat_tiedot"),
    ("varallisuus täsmälleen rajalla", [42000], "kelpoinen"),
    ("euron rajan yli", [42001], "ei_kelpoinen"),
    ("ruokakunnan varallisuus lasketaan yhteen", [30000, 30000], "ei_kelpoinen"),
]


@pytest.mark.parametrize(
    ("assets", "expected"),
    [(c[1], c[2]) for c in VARALLISUUS_CASES],
    ids=[c[0] for c in VARALLISUUS_CASES],
)
def test_assets_within_limit(assets: list[int | None], expected: str) -> None:
    snapshot = application(members=tuple(member(assets=a) for a in assets))
    outcome = assets_within_limit(snapshot, unit(housing_form=TARVE), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "TARVE-VARALLISUUS-01"
    assert outcome.evidence["varallisuusraja_eur"] == 42000


TARVE_CASES = [
    ("asunnoton", "asunnoton", "kelpoinen"),
    ("vuokrasopimus irtisanottu", "irtisanottu", "kelpoinen"),
    ("asuu ahtaasti", "ahtaasti", "kelpoinen"),
    ("ei erityistä tarvetta on kelvollinen vastaus", "ei_tarvetta", "kelpoinen"),
    ("tarvetta ei ole ilmoitettu", None, "puuttuvat_tiedot"),
]


@pytest.mark.parametrize(
    ("situation", "expected"),
    [(c[1], c[2]) for c in TARVE_CASES],
    ids=[c[0] for c in TARVE_CASES],
)
def test_housing_need_stated(situation: str | None, expected: str) -> None:
    outcome = housing_need_stated(
        application(housing_need=situation), unit(housing_form=TARVE), LIMITS
    )

    assert outcome.outcome == expected
    assert outcome.rule_id == "TARVE-TARVE-01"


def test_no_special_need_is_not_a_rejection() -> None:
    """Stating "no special need" answers the question; it does not fail the rule.

    It changes where the applicant lands in the queue, and the message says so.
    """
    outcome = housing_need_stated(
        application(housing_need="ei_tarvetta"), unit(housing_form=TARVE), LIMITS
    )

    assert outcome.outcome == "kelpoinen"
    assert outcome.evidence["vaikuttaa_jarjestykseen"] is True
    assert "järjestykseen" in outcome.message_fi


def _applicant(
    id: int,
    *,
    need: str | None,
    assets: int,
    income: int,
    days_ago: int = 10,
) -> object:
    return application(
        id=id,
        housing_need=need,
        members=(member(assets=assets, income=income),),
        created_at=NOW - dt.timedelta(days=days_ago),
    )


def test_ranking_orders_by_need_then_wealth_then_income() -> None:
    """The three ranking dimensions, each one decisive in turn."""
    homeless = _applicant(1, need="asunnoton", assets=40000, income=3000)
    crowded_poor = _applicant(2, need="ahtaasti", assets=1000, income=2000)
    crowded_richer = _applicant(3, need="ahtaasti", assets=20000, income=1000)
    crowded_same_wealth_more_income = _applicant(4, need="ahtaasti", assets=1000, income=2500)

    ranked = needs_ranking(
        [crowded_richer, crowded_same_wealth_more_income, homeless, crowded_poor],
        unit(housing_form=TARVE),
        LIMITS,
    )

    assert [r.application_id for r in ranked] == [1, 2, 4, 3]
    assert [r.rank for r in ranked] == [1, 2, 3, 4]


def test_ranking_breaks_ties_by_submission_date_not_randomly() -> None:
    earlier = _applicant(7, need="ahtaasti", assets=5000, income=2000, days_ago=30)
    later = _applicant(8, need="ahtaasti", assets=5000, income=2000, days_ago=3)

    forwards = needs_ranking([earlier, later], unit(housing_form=TARVE), LIMITS)
    backwards = needs_ranking([later, earlier], unit(housing_form=TARVE), LIMITS)

    assert [r.application_id for r in forwards] == [7, 8]
    assert [r.application_id for r in backwards] == [7, 8]


def test_ranking_explains_each_position() -> None:
    """The admin view has to show why A ranks above B on all three dimensions."""
    ranked = needs_ranking(
        [
            _applicant(1, need="asunnoton", assets=1000, income=1500),
            _applicant(2, need="ei_tarvetta", assets=1000, income=1500),
        ],
        unit(housing_form=TARVE),
        LIMITS,
    )

    first = ranked[0]
    assert first.evidence["asunnontarve"] == "asunnoton"
    assert first.evidence["ruokakunnan_varallisuus_eur"] == 1000
    assert first.evidence["ruokakunnan_bruttotulot_eur_kk"] == 1500
    assert first.evidence["hakemus_jatetty"]
    assert "Sija 1" in first.message_fi


def test_applicants_with_missing_data_are_ranked_last_not_dropped() -> None:
    complete = _applicant(1, need="ahtaasti", assets=9000, income=2000)
    incomplete = application(
        id=2,
        housing_need=None,
        members=(member(assets=None, income=None),),
        created_at=NOW - dt.timedelta(days=60),
    )

    ranked = needs_ranking([incomplete, complete], unit(housing_form=TARVE), LIMITS)

    assert [r.application_id for r in ranked] == [1, 2]
    assert ranked[1].evidence["asunnontarve"] is None
