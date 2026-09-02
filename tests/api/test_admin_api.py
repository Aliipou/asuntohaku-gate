"""The tenant selection view: ranked applicants and the basis for the order."""

from __future__ import annotations

from sqlalchemy import text

from tests.api.conftest import requires_db

pytestmark = requires_db


def _applicant(
    client,  # noqa: ANN001
    unit_id: int,
    *,
    name: str,
    need: str,
    assets: str,
    income: str,
    order_number: str | None = None,
) -> str:
    token = client.post("/api/applications", json={"contact_name": name}).json()["edit_token"]
    client.put(
        f"/api/applications/{token}",
        json={
            "members": [
                {
                    "role": "paahakija",
                    "birth_year": 1985,
                    "gross_monthly_income_eur": income,
                    "assets_eur": assets,
                }
            ],
            "housing_need": {"situation": need},
            "order_number": order_number,
            "deposit_acknowledged": True,
            "credit_default_flag": False,
        },
    )
    client.post(f"/api/applications/{token}/units", json={"unit_id": unit_id})
    return token


def test_needs_assessed_ranking_shows_all_three_dimensions(client, unit_ids) -> None:  # noqa: ANN001
    """SPEC section 7.5: show why A ranks above B, not just that it does."""
    unit_id = unit_ids["tarveharkintainen"]
    _applicant(client, unit_id, name="Bea", need="ahtaasti", assets="9000", income="2000")
    _applicant(client, unit_id, name="Aki", need="asunnoton", assets="12000", income="2400")

    body = client.get(f"/api/admin/units/{unit_id}/applicants").json()

    assert body["ranking_rule_id"] == "TARVE-SIJOITUS-01"
    assert body["ranking_basis_fi"]
    assert [a["contact_name"] for a in body["applicants"]] == ["Aki", "Bea"]

    first = body["applicants"][0]
    keys = {item["avain"] for item in first["evidence"]}
    assert keys >= {
        "asunnontarve",
        "ruokakunnan_varallisuus_eur",
        "ruokakunnan_bruttotulot_eur_kk",
        "hakemus_jatetty",
    }


def test_ranking_shows_eligibility_alongside_the_order(client, unit_ids) -> None:  # noqa: ANN001
    """Being first in the queue is not the same as being eligible; show both."""
    unit_id = unit_ids["tarveharkintainen"]
    _applicant(client, unit_id, name="Yli rajan", need="asunnoton", assets="90000", income="2000")

    applicant = client.get(f"/api/admin/units/{unit_id}/applicants").json()["applicants"][0]

    assert applicant["rank"] == 1
    assert applicant["eligibility"] == "ei_kelpoinen"
    assert "varallisuusrajan" in applicant["eligibility_message_fi"]


def test_right_of_occupancy_ranks_by_order_number(client, unit_ids) -> None:  # noqa: ANN001
    unit_id = unit_ids["asumisoikeus"]
    _applicant(
        client,
        unit_id,
        name="Suuri numero",
        need="ahtaasti",
        assets="1000",
        income="2000",
        order_number="912000",
    )
    _applicant(
        client,
        unit_id,
        name="Pieni numero",
        need="ahtaasti",
        assets="1000",
        income="2000",
        order_number="000199",
    )

    body = client.get(f"/api/admin/units/{unit_id}/applicants").json()

    assert body["ranking_rule_id"] == "ASO-JARJ-02"
    assert [a["contact_name"] for a in body["applicants"]] == ["Pieni numero", "Suuri numero"]


def test_an_applicant_without_an_order_number_is_not_in_the_queue(client, unit_ids) -> None:  # noqa: ANN001
    """ASO-JARJ-01 has already stopped them, so they do not appear ranked."""
    unit_id = unit_ids["asumisoikeus"]
    _applicant(client, unit_id, name="Ei numeroa", need="ahtaasti", assets="1000", income="2000")

    body = client.get(f"/api/admin/units/{unit_id}/applicants").json()

    assert body["applicants"] == []
    assert body["ranking_rule_id"] == "ASO-JARJ-02"


def test_free_financed_stock_is_not_ranked(client, unit_ids) -> None:  # noqa: ANN001
    """Open stock has no ranking rule, and the view says so rather than inventing one."""
    unit_id = unit_ids["vapaarahoitteinen"]
    _applicant(client, unit_id, name="Hakija", need="ahtaasti", assets="1000", income="2500")

    body = client.get(f"/api/admin/units/{unit_id}/applicants").json()

    assert body["ranking_rule_id"] is None
    assert body["applicants"] == []


def test_ranking_is_stable_across_calls(client, unit_ids) -> None:  # noqa: ANN001
    """Ties break on submission time, never randomly."""
    unit_id = unit_ids["tarveharkintainen"]
    for name in ("Ensimmainen", "Toinen", "Kolmas"):
        _applicant(client, unit_id, name=name, need="ahtaasti", assets="5000", income="2000")

    first = client.get(f"/api/admin/units/{unit_id}/applicants").json()
    second = client.get(f"/api/admin/units/{unit_id}/applicants").json()

    order = [a["contact_name"] for a in first["applicants"]]
    assert order == [a["contact_name"] for a in second["applicants"]]
    assert order == ["Ensimmainen", "Toinen", "Kolmas"]


def test_unknown_unit_404s(client, seeded) -> None:  # noqa: ANN001
    assert client.get("/api/admin/units/999999/applicants").status_code == 404


def test_the_admin_view_needs_no_credentials(client, unit_ids, engine) -> None:  # noqa: ANN001
    """Stated plainly rather than hidden: access control is out of scope.

    This test exists so the absence is deliberate and visible, not an oversight
    someone discovers later.
    """
    response = client.get(f"/api/admin/units/{unit_ids['tarveharkintainen']}/applicants")

    assert response.status_code == 200
    with engine.connect() as connection:
        tables = connection.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        ).scalars()
    assert not any("user" in name or "session" in name for name in tables)
