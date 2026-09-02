"""VAPAA-MAKSU-01, VAPAA-VAKUUS-01, VAPAA-LUOTTO-01."""

from __future__ import annotations

import itertools

import pytest

from api.rules.vapaarahoitteinen import credit_record, deposit_acknowledged, rent_within_income
from api.texts import fi
from tests.conftest import LIMITS, application, member, unit

VAPAA = "vapaarahoitteinen"

# Limit in play: rent may take at most 35 % of gross monthly household income.
MAKSU_CASES = [
    # id, member incomes, rent, expected
    ("tulot riittävät", [3000], 900, "kelpoinen"),
    ("tulot eivät riitä", [2000], 900, "ei_kelpoinen"),
    ("tulot puuttuvat", [None], 900, "puuttuvat_tiedot"),
    ("yhden jäsenen tulot puuttuvat", [2000, None], 900, "puuttuvat_tiedot"),
    ("vuokra täsmälleen enimmäisosuus", [2000], 700, "kelpoinen"),
    ("vuokra euron yli rajan", [2000], 701, "ei_kelpoinen"),
]


@pytest.mark.parametrize(
    ("incomes", "rent", "expected"),
    [(c[1], c[2], c[3]) for c in MAKSU_CASES],
    ids=[c[0] for c in MAKSU_CASES],
)
def test_rent_within_income(incomes: list[int | None], rent: int, expected: str) -> None:
    snapshot = application(members=tuple(member(income=i) for i in incomes))
    outcome = rent_within_income(snapshot, unit(housing_form=VAPAA, rent=rent), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "VAPAA-MAKSU-01"
    assert outcome.evidence


def test_benefit_income_is_not_treated_differently() -> None:
    """The rule has no way to tell where income comes from, and must not gain one.

    Same household total, split differently: one earner, or two people whose
    income happens to be benefits. The outcome and the decisive number are
    identical.
    """
    one_earner = application(members=(member(income=3000),))
    two_people = application(members=(member(income=1500), member(role="toinen", income=1500)))
    rental = unit(housing_form=VAPAA, rent=900)

    first = rent_within_income(one_earner, rental, LIMITS)
    second = rent_within_income(two_people, rental, LIMITS)

    assert first.outcome == second.outcome == "kelpoinen"
    assert (
        first.evidence["ruokakunnan_bruttotulot_eur_kk"]
        == second.evidence["ruokakunnan_bruttotulot_eur_kk"]
    )


def test_rent_failure_names_the_affordable_rent() -> None:
    """A refusal has to be actionable: it says what rent these incomes do reach."""
    snapshot = application(members=(member(income=2000),))
    outcome = rent_within_income(snapshot, unit(housing_form=VAPAA, rent=900), LIMITS)

    assert outcome.outcome == "ei_kelpoinen"
    assert outcome.evidence["enimmaisvuokra_eur_kk"] == 700
    assert f"700{fi.NBSP}€" in outcome.message_fi


def test_rent_rule_rejects_a_sale_unit() -> None:
    """Sale units are offered on, not applied for. Reaching this rule is a bug."""
    with pytest.raises(ValueError, match="not a rental unit"):
        rent_within_income(
            application(),
            unit(housing_form=VAPAA, listing_type="myynti", rent=None, price=250000),
            LIMITS,
        )


VAKUUS_CASES = [
    ("vakuus hyväksytty", True, 900, "kelpoinen"),
    ("vakuutta ei hyväksytty", False, 900, "ei_kelpoinen"),
    ("vakuutta ei ole vahvistettu", None, 900, "puuttuvat_tiedot"),
    ("vakuuden määrää ei ole kirjattu", None, None, "puuttuvat_tiedot"),
]


@pytest.mark.parametrize(
    ("acknowledged", "deposit", "expected"),
    [(c[1], c[2], c[3]) for c in VAKUUS_CASES],
    ids=[c[0] for c in VAKUUS_CASES],
)
def test_deposit_acknowledged(
    acknowledged: bool | None, deposit: int | None, expected: str
) -> None:
    outcome = deposit_acknowledged(
        application(deposit_acknowledged=acknowledged),
        unit(housing_form=VAPAA, deposit=deposit),
        LIMITS,
    )

    assert outcome.outcome == expected
    assert outcome.rule_id == "VAPAA-VAKUUS-01"


LUOTTO_CASES = [
    ("ei merkintää", False, "kelpoinen"),
    ("merkintä on", True, "puuttuvat_tiedot"),
    ("luottotietoja ei ole kysytty", None, "puuttuvat_tiedot"),
]


@pytest.mark.parametrize(
    ("flag", "expected"),
    [(c[1], c[2]) for c in LUOTTO_CASES],
    ids=[c[0] for c in LUOTTO_CASES],
)
def test_credit_record(flag: bool | None, expected: str) -> None:
    outcome = credit_record(application(credit_default_flag=flag), unit(housing_form=VAPAA), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "VAPAA-LUOTTO-01"


def test_credit_default_asks_for_context_and_never_rejects() -> None:
    """The asymmetry in VAPAA-LUOTTO-01, asserted rather than described.

    A default marker must not be able to produce ei_kelpoinen through any input,
    and the marker case has to be distinguishable from the unanswered case, or
    the applicant is asked the wrong question.
    """
    rental = unit(housing_form=VAPAA)
    outcomes = [
        credit_record(application(credit_default_flag=flag), rental, LIMITS)
        for flag in (True, False, None)
    ]

    assert all(o.outcome != "ei_kelpoinen" for o in outcomes)

    with_marker, _, unanswered = outcomes
    assert with_marker.evidence["maksuhairiomerkinta"] is True
    assert with_marker.evidence["pyydetty_lisatieto"]
    assert unanswered.evidence["puuttuva_tieto"] == "luottotiedot"
    assert with_marker.message_fi != unanswered.message_fi


def test_free_financed_rules_ask_for_no_means_testing() -> None:
    """Open stock: the form must never grow a wealth or need section because of it."""
    from api.rules.registry import rules_for_form

    requires = set(itertools.chain.from_iterable(r.meta.requires for r in rules_for_form(VAPAA)))

    assert "assets" not in requires
    assert "housing_need" not in requires
