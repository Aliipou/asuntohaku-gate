"""The seed stock, checked against what the schema and the specification require.

These run without a database: the point is to catch a bad row before it reaches
a check constraint in CI, and to keep the demo stock the shape SPEC section 8
describes.
"""

from __future__ import annotations

from seeds.data import PROPERTIES

RENTAL = [u for p in PROPERTIES for u in p.units if u.listing_type == "vuokra"]
SALE = [u for p in PROPERTIES for u in p.units if u.listing_type == "myynti"]


def test_stock_matches_the_shape_the_specification_asks_for() -> None:
    assert len(PROPERTIES) == 8
    assert len(RENTAL) == 40
    assert len(SALE) == 8


def test_all_four_housing_forms_and_all_four_cities_are_represented() -> None:
    assert {p.housing_form for p in PROPERTIES} == {
        "vapaarahoitteinen",
        "lyhyt_korkotuki",
        "tarveharkintainen",
        "asumisoikeus",
    }
    assert {p.city for p in PROPERTIES} == {"Helsinki", "Espoo", "Vantaa", "Tampere"}


def test_availability_is_mixed() -> None:
    assert {u.availability for p in PROPERTIES for u in p.units} == {
        "vapaa",
        "vapautuu",
        "sopimuksella",
    }


def test_rent_and_price_satisfy_the_check_constraint() -> None:
    """ck_units_listing_price, asserted before PostgreSQL gets the chance to."""
    for unit in RENTAL:
        assert unit.rent_eur is not None and unit.price_eur is None, unit.unit_number
    for unit in SALE:
        assert unit.price_eur is not None and unit.rent_eur is None, unit.unit_number


def test_rental_units_carry_a_deposit() -> None:
    """VAPAA-VAKUUS-01 asks the applicant to accept a specific sum."""
    assert all(u.deposit_eur is not None for u in RENTAL)


def test_units_are_uniquely_numbered_within_a_property() -> None:
    for prop in PROPERTIES:
        numbers = [u.unit_number for u in prop.units]
        assert len(numbers) == len(set(numbers)), prop.name


def test_sale_stock_is_free_financed_only() -> None:
    """Regulated stock is allocated, not sold on the open market in this demo."""
    for prop in PROPERTIES:
        if any(u.listing_type == "myynti" for u in prop.units):
            assert prop.housing_form == "vapaarahoitteinen", prop.name


def test_descriptions_are_written_not_generated() -> None:
    """No placeholder text, and no two apartments sharing a description."""
    descriptions = [u.description_fi for p in PROPERTIES for u in p.units]

    assert len(descriptions) == len(set(descriptions))
    for text in descriptions:
        assert len(text) > 60
        assert "lorem" not in text.lower()
        assert "TODO" not in text


def test_the_stock_can_exercise_the_size_rule() -> None:
    """Scenario 7 needs a studio to reject a five-person household with."""
    assert any(u.rooms == 1 for u in RENTAL)
    assert any(u.rooms >= 4 for u in RENTAL)
