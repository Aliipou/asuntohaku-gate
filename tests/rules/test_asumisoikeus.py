"""ASO-JARJ-01, ASO-JARJ-02, ASO-VARALLISUUS-01."""

from __future__ import annotations

import pytest

from api.rules.asumisoikeus import (
    assets_within_limit_unless_exempt,
    order_number_present,
    order_number_ranking,
)
from tests.conftest import LIMITS, NOW, application, member, unit

ASO = "asumisoikeus"
BIRTH_YEAR_FOR_AGE = NOW.year  # subtract the wanted age

JARJ_CASES = [
    ("numero on oikean muotoinen", "123456", "kelpoinen"),
    ("numero puuttuu", None, "puuttuvat_tiedot"),
    ("tyhjä numero on puuttuva tieto", "   ", "puuttuvat_tiedot"),
    ("liian lyhyt numero", "12345", "ei_kelpoinen"),
    ("liian pitkä numero", "1234567", "ei_kelpoinen"),
    ("kirjaimia numerossa", "12A456", "ei_kelpoinen"),
]


@pytest.mark.parametrize(
    ("number", "expected"),
    [(c[1], c[2]) for c in JARJ_CASES],
    ids=[c[0] for c in JARJ_CASES],
)
def test_order_number_present(number: str | None, expected: str) -> None:
    outcome = order_number_present(application(order_number=number), unit(housing_form=ASO), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "ASO-JARJ-01"


def test_missing_order_number_is_not_a_rejection() -> None:
    """Scenario 5: choosing a right-of-occupancy apartment without a number yet."""
    outcome = order_number_present(application(order_number=None), unit(housing_form=ASO), LIMITS)

    assert outcome.outcome == "puuttuvat_tiedot"
    assert outcome.evidence["puuttuva_tieto"] == "asumisoikeusnumero"


def test_ranking_is_ascending_by_order_number() -> None:
    applicants = [
        application(id=1, order_number="004512"),
        application(id=2, order_number="000199"),
        application(id=3, order_number="912000"),
    ]

    ranked = order_number_ranking(applicants, unit(housing_form=ASO), LIMITS)

    assert [r.application_id for r in ranked] == [2, 1, 3]
    assert [r.evidence["asumisoikeusnumero"] for r in ranked] == ["000199", "004512", "912000"]


def test_ranking_excludes_applicants_without_a_usable_number() -> None:
    """They are not in the queue: ASO-JARJ-01 has already stopped them."""
    applicants = [
        application(id=1, order_number="000199"),
        application(id=2, order_number=None),
        application(id=3, order_number="12345"),
    ]

    ranked = order_number_ranking(applicants, unit(housing_form=ASO), LIMITS)

    assert [r.application_id for r in ranked] == [1]


def _household(*ages: int, assets: int | None = 10000) -> object:
    """A household of the given ages, sharing the household assets equally."""
    per_person = None if assets is None else assets // len(ages)
    return application(
        members=tuple(
            member(
                role="paahakija" if index == 0 else "toinen",
                birth_year=BIRTH_YEAR_FOR_AGE - age,
                assets=per_person,
            )
            for index, age in enumerate(ages)
        )
    )


# Limit in play: 95 000 € household assets, exemption from age 55.
VARALLISUUS_CASES = [
    ("varallisuus rajan alle", (40,), 50000, "kelpoinen"),
    ("varallisuus rajan yli", (40,), 120000, "ei_kelpoinen"),
    ("varallisuus puuttuu", (40,), None, "puuttuvat_tiedot"),
    ("varallisuus täsmälleen rajalla", (40,), 95000, "kelpoinen"),
    ("euron rajan yli", (40,), 95002, "ei_kelpoinen"),
    ("täsmälleen 55-vuotias on vapautettu", (55,), 120000, "kelpoinen"),
    ("54-vuotias ei ole vapautettu", (54,), 120000, "ei_kelpoinen"),
    ("kaikkien aikuisten oltava vapautettuja", (56, 54), 120000, "ei_kelpoinen"),
    ("kaksi vapautettua aikuista", (56, 61), 120000, "kelpoinen"),
]


@pytest.mark.parametrize(
    ("ages", "assets", "expected"),
    [(c[1], c[2], c[3]) for c in VARALLISUUS_CASES],
    ids=[c[0] for c in VARALLISUUS_CASES],
)
def test_assets_within_limit_unless_exempt(
    ages: tuple[int, ...], assets: int | None, expected: str
) -> None:
    outcome = assets_within_limit_unless_exempt(
        _household(*ages, assets=assets), unit(housing_form=ASO), LIMITS
    )

    assert outcome.outcome == expected
    assert outcome.rule_id == "ASO-VARALLISUUS-01"


def test_exemption_names_itself_in_the_evidence() -> None:
    """Section 5 asks for the exemption to be named, not silently applied."""
    outcome = assets_within_limit_unless_exempt(
        _household(55, 58, assets=200000), unit(housing_form=ASO), LIMITS
    )

    assert outcome.outcome == "kelpoinen"
    assert outcome.evidence["poikkeus"] == "ikapoikkeus"
    assert outcome.evidence["vapautusika"] == 55
    assert outcome.evidence["aikuisten_iat"] == [55, 58]
    assert "55" in outcome.message_fi


def test_children_do_not_block_the_exemption() -> None:
    """The exemption is about adult applicants, so a child in the household is irrelevant."""
    outcome = assets_within_limit_unless_exempt(
        _household(58, 12, assets=200000), unit(housing_form=ASO), LIMITS
    )

    assert outcome.outcome == "kelpoinen"
    assert outcome.evidence["aikuisten_iat"] == [58]


def test_assets_over_limit_with_unknown_ages_is_a_question_not_a_refusal() -> None:
    """We cannot tell whether the exemption applies, so we ask for the birth years."""
    snapshot = application(members=(member(birth_year=None, assets=200000),))

    outcome = assets_within_limit_unless_exempt(snapshot, unit(housing_form=ASO), LIMITS)

    assert outcome.outcome == "puuttuvat_tiedot"
    assert outcome.evidence["puuttuva_tieto"] == "syntymavuodet"


def test_right_of_occupancy_has_no_income_limit() -> None:
    """No income rule may be registered for this housing form."""
    from api.rules.registry import rules_for_form

    income_rules = [r.meta.id for r in rules_for_form(ASO) if "household_income" in r.meta.requires]

    assert income_rules == []
