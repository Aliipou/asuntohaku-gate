"""YLEIS-KOKO-01 and YLEIS-VANHENTUNUT-01."""

from __future__ import annotations

import datetime as dt

import pytest

from api.rules.yleiset import application_still_valid, household_fits_unit
from tests.conftest import LIMITS, NOW, application, member, unit

# Limits in play: at most two people per room, and an apartment counts as large
# for the household when it has two rooms more than there are people.
KOKO_CASES = [
    # id, household size, rooms, expected, expected note in the evidence
    ("kahden hengen ruokakunta kahden huoneen asuntoon", 2, 2, "kelpoinen", False),
    ("viisi henkeä yksiöön", 5, 1, "ei_kelpoinen", False),
    ("täsmälleen enimmäiskoko yksiössä", 2, 1, "kelpoinen", False),
    ("yksi henkilö enimmäiskoon yli", 3, 1, "ei_kelpoinen", False),
    ("yksin neljän huoneen asuntoon", 1, 4, "kelpoinen", True),
    ("yksin kahden huoneen asuntoon ei ole huomautettavaa", 1, 2, "kelpoinen", False),
    ("ruokakuntaa ei ole ilmoitettu", 0, 2, "puuttuvat_tiedot", False),
]


@pytest.mark.parametrize(
    ("size", "rooms", "expected", "expect_note"),
    [(c[1], c[2], c[3], c[4]) for c in KOKO_CASES],
    ids=[c[0] for c in KOKO_CASES],
)
def test_household_fits_unit(size: int, rooms: int, expected: str, expect_note: bool) -> None:
    snapshot = application(members=tuple(member(role="muu") for _ in range(size)))

    outcome = household_fits_unit(snapshot, unit(rooms=rooms), LIMITS)

    assert outcome.outcome == expected
    assert outcome.rule_id == "YLEIS-KOKO-01"
    assert ("huomautus" in outcome.evidence) is expect_note


def test_too_large_a_household_is_told_the_maximum() -> None:
    """Scenario 7: a five-person household applying for a studio."""
    snapshot = application(members=tuple(member(role="muu") for _ in range(5)))

    outcome = household_fits_unit(snapshot, unit(rooms=1, area_m2=28), LIMITS)

    assert outcome.outcome == "ei_kelpoinen"
    assert outcome.evidence["enimmaiskoko"] == 2
    assert outcome.evidence["ruokakunnan_koko"] == 5
    assert "enintään 2" in outcome.message_fi


def test_a_large_apartment_is_a_note_and_not_a_refusal() -> None:
    outcome = household_fits_unit(application(members=(member(),)), unit(rooms=4), LIMITS)

    assert outcome.outcome == "kelpoinen"
    assert outcome.evidence["huomautus"] == "asunto_suuri_ruokakuntaan_nahden"


VANHENTUNUT_CASES = [
    ("voimassa", -30, "kelpoinen"),
    ("vanhentunut", 1, "puuttuvat_tiedot"),
    ("umpeutuu tasan nyt", 0, "kelpoinen"),
    ("sekunti umpeutumisen jälkeen", None, "puuttuvat_tiedot"),
]


@pytest.mark.parametrize(
    ("days_past_expiry", "expected"),
    [(c[1], c[2]) for c in VANHENTUNUT_CASES],
    ids=[c[0] for c in VANHENTUNUT_CASES],
)
def test_application_still_valid(days_past_expiry: int | None, expected: str) -> None:
    if days_past_expiry is None:
        expires_at = NOW - dt.timedelta(seconds=1)
    else:
        expires_at = NOW - dt.timedelta(days=days_past_expiry)

    outcome = application_still_valid(
        application(created_at=NOW - dt.timedelta(days=120), expires_at=expires_at),
        unit(),
        LIMITS,
    )

    assert outcome.outcome == expected
    assert outcome.rule_id == "YLEIS-VANHENTUNUT-01"


def test_expired_application_points_at_the_edit_link() -> None:
    """Scenario 8: four months old. Expiry is a request to confirm, not a rejection."""
    created = NOW - dt.timedelta(days=122)
    outcome = application_still_valid(
        application(created_at=created, expires_at=created + dt.timedelta(days=92)),
        unit(),
        LIMITS,
    )

    assert outcome.outcome == "puuttuvat_tiedot"
    assert outcome.evidence["voimassa_asti"] == created + dt.timedelta(days=92)
    assert "muokkauslinkki" in outcome.message_fi
