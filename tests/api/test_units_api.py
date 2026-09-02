"""GET /api/units and /api/units/{id}, including the 404 path."""

from __future__ import annotations

from decimal import Decimal

from tests.api.conftest import requires_db

pytestmark = requires_db


def test_search_returns_the_whole_seeded_stock(client, seeded) -> None:  # noqa: ANN001
    body = client.get("/api/units", params={"limit": 200}).json()

    assert body["total"] == 48
    assert len(body["units"]) == 48
    assert {u["listing_type"] for u in body["units"]} == {"vuokra", "myynti"}


def test_rental_and_sale_stock_share_one_index(client, seeded) -> None:  # noqa: ANN001
    """One grid, distinguished by structure: a sale row has a price and no rent."""
    units = client.get("/api/units", params={"limit": 200}).json()["units"]

    for unit in units:
        if unit["listing_type"] == "vuokra":
            assert unit["rent_eur"] is not None and unit["price_eur"] is None
        else:
            assert unit["price_eur"] is not None and unit["rent_eur"] is None


def test_filters_narrow_the_result(client, seeded) -> None:  # noqa: ANN001
    helsinki = client.get("/api/units", params={"city": "Helsinki"}).json()
    aso = client.get("/api/units", params={"housing_form": "asumisoikeus"}).json()
    small = client.get("/api/units", params={"rooms_max": 1, "listing_type": "vuokra"}).json()

    assert helsinki["total"] < 48
    assert {u["city"] for u in helsinki["units"]} == {"Helsinki"}
    assert {u["housing_form"] for u in aso["units"]} == {"asumisoikeus"}
    assert all(u["rooms"] == 1 for u in small["units"])


def test_rent_range_filter_uses_numbers_not_strings(client, seeded) -> None:  # noqa: ANN001
    body = client.get(
        "/api/units", params={"listing_type": "vuokra", "rent_min": 900, "rent_max": 1100}
    ).json()

    assert body["total"] >= 1
    for unit in body["units"]:
        assert Decimal("900") <= Decimal(unit["rent_eur"]) <= Decimal("1100")


def test_filters_that_match_nothing_return_an_empty_result_not_an_error(client, seeded) -> None:  # noqa: ANN001
    body = client.get("/api/units", params={"city": "Oulu"}).json()

    assert body["total"] == 0
    assert body["units"] == []


def test_detail_explains_what_the_housing_form_means(client, unit_ids) -> None:  # noqa: ANN001
    """SPEC section 7.2: one sentence saying what the form means for the applicant."""
    unit_id = unit_ids["tarveharkintainen"]

    body = client.get(f"/api/units/{unit_id}").json()

    assert body["housing_form"] == "tarveharkintainen"
    assert body["housing_form_label_fi"] == "tarveharkintainen vuokra-asunto"
    assert "asunnontarve" in body["housing_form_explanation_fi"]
    assert body["description_fi"]


def test_unknown_unit_is_a_finnish_404(client, seeded) -> None:  # noqa: ANN001
    response = client.get("/api/units/999999")

    assert response.status_code == 404
    assert "Asuntoa ei löytynyt" in response.json()["detail"]


def test_offers_are_refused_for_rental_stock(client, unit_ids) -> None:  # noqa: ANN001
    response = client.post(
        f"/api/units/{unit_ids['vapaarahoitteinen']}/offers",
        json={"contact_name": "Ostaja", "contact_email": "ostaja@esimerkki.fi", "amount_eur": 1},
    )

    assert response.status_code == 400
    assert "myytävästä" in response.json()["detail"]


def test_offer_on_a_sale_unit_is_accepted(client, unit_ids) -> None:  # noqa: ANN001
    response = client.post(
        f"/api/units/{unit_ids['myynti']}/offers",
        json={
            "contact_name": "Ostaja Esimerkki",
            "contact_email": "ostaja@esimerkki.fi",
            "amount_eur": 315000,
            "message": "Tarjous voimassa kaksi viikkoa.",
        },
    )

    assert response.status_code == 201
    assert Decimal(response.json()["amount_eur"]) == Decimal("315000")


def test_offer_amount_must_be_positive(client, unit_ids) -> None:  # noqa: ANN001
    response = client.post(
        f"/api/units/{unit_ids['myynti']}/offers",
        json={"contact_name": "Ostaja", "contact_email": "o@esimerkki.fi", "amount_eur": 0},
    )

    assert response.status_code == 422
