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


# -- listing content (seeds/listings.py) -----------------------------------
# Section 8 makes this content a real requirement rather than a placeholder
# task: a search page laid out against thin data looks broken however good the
# code is. These tests hold the content to the bar the spec sets.

from seeds.listings import PROPERTY_CONTACTS, PROPERTY_COORDINATES, UNIT_LISTINGS  # noqa: E402

UNIT_KEYS = {(p.name, u.unit_number) for p in PROPERTIES for u in p.units}
UNITS_BY_KEY = {(p.name, u.unit_number): u for p in PROPERTIES for u in p.units}


def test_every_unit_has_listing_content() -> None:
    assert set(UNIT_LISTINGS) == UNIT_KEYS
    assert set(PROPERTY_CONTACTS) == {p.name for p in PROPERTIES}
    assert set(PROPERTY_COORDINATES) == {p.name for p in PROPERTIES}


def test_every_unit_has_photographs_and_exactly_one_floor_plan() -> None:
    for key, listing in UNIT_LISTINGS.items():
        assert len(listing.images) >= 3, key
        plans = [i for i in listing.images if i.kind == "pohjapiirros"]
        assert len(plans) == 1, key
        assert len({i.url for i in listing.images}) == len(listing.images), key
        assert len({i.sort_order for i in listing.images}) == len(listing.images), key


def test_every_image_is_attributed() -> None:
    """Stock photos under a licence: the credit has to survive into the database."""
    for key, listing in UNIT_LISTINGS.items():
        for image in listing.images:
            assert image.credit.strip(), key
            assert image.alt_fi.strip(), key
            assert image.url.startswith("https://"), key


def test_descriptions_are_substantial_and_distinct() -> None:
    descriptions = [listing.description_fi for listing in UNIT_LISTINGS.values()]

    assert len(set(descriptions)) == len(descriptions)
    for text in descriptions:
        assert text.count(".") >= 4, text[:60]
        assert len(text) >= 300
        assert "lorem" not in text.lower()


def test_room_layout_matches_the_room_count() -> None:
    """`2h + kk + s` has to agree with the `rooms` column, or the row lies."""
    for key, listing in UNIT_LISTINGS.items():
        assert listing.room_layout_fi.startswith(f"{UNITS_BY_KEY[key].rooms}h"), key


def test_maintenance_fee_is_a_sale_only_fact() -> None:
    """Matches the ck_units_maintenance_fee constraint, checked before the database."""
    for key, listing in UNIT_LISTINGS.items():
        is_sale = UNITS_BY_KEY[key].listing_type == "myynti"
        assert (listing.maintenance_fee_eur is not None) is is_sale, key


def test_coordinates_are_distinct_so_map_pins_do_not_stack() -> None:
    points = {(c.lat, c.lng) for c in PROPERTY_COORDINATES.values()}

    assert len(points) == len(PROPERTY_COORDINATES)


def test_every_property_has_a_named_contact_with_a_photo() -> None:
    for name, contact in PROPERTY_CONTACTS.items():
        assert contact.name.strip() and contact.title_fi.strip(), name
        assert contact.email.endswith("asuntohaku-demo.fi"), name
        assert contact.photo_url, name
