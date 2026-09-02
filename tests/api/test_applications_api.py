"""The application flow: create, edit, basket, adaptive fields, decisions."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import text

from tests.api.conftest import requires_db

pytestmark = requires_db


def test_creating_an_application_returns_an_edit_token(client, seeded) -> None:  # noqa: ANN001
    response = client.post("/api/applications", json={"contact_name": "Aino Virtanen"})

    assert response.status_code == 201
    body = response.json()
    assert len(body["edit_token"]) == 36
    assert body["status"] == "luonnos"
    assert not body["expired"]


def test_expiry_is_three_months_from_creation(client, seeded) -> None:  # noqa: ANN001
    body = client.post("/api/applications", json={}).json()

    created = dt.datetime.fromisoformat(body["created_at"])
    expires = dt.datetime.fromisoformat(body["expires_at"])
    assert 89 <= (expires - created).days <= 92


def test_unknown_and_malformed_tokens_both_404(client, seeded) -> None:  # noqa: ANN001
    """A malformed token must not leak that it was malformed rather than unknown."""
    unknown = client.get("/api/applications/2b1f8f0e-0000-4000-8000-000000000000")
    malformed = client.get("/api/applications/not-a-uuid")

    assert unknown.status_code == malformed.status_code == 404
    assert unknown.json()["detail"] == malformed.json()["detail"]


def test_the_form_is_filled_in_over_several_visits(client, application_token) -> None:  # noqa: ANN001
    """Every field is optional on update: a half-filled form must be savable."""
    first = client.put(
        f"/api/applications/{application_token}",
        json={"members": [{"role": "paahakija", "birth_year": 1990}]},
    )
    assert first.status_code == 200

    second = client.put(
        f"/api/applications/{application_token}",
        json={
            "members": [
                {"role": "paahakija", "birth_year": 1990, "gross_monthly_income_eur": "3000"}
            ]
        },
    )

    assert second.status_code == 200
    member = second.json()["members"][0]
    # Money comes back with the column's scale (NUMERIC(10,2)), so compare as
    # Decimal rather than as a string.
    assert Decimal(member["gross_monthly_income_eur"]) == Decimal("3000")
    assert member["birth_year"] == 1990


def test_adding_and_removing_an_apartment(client, application_token, unit_ids) -> None:  # noqa: ANN001
    unit_id = unit_ids["vapaarahoitteinen"]

    added = client.post(f"/api/applications/{application_token}/units", json={"unit_id": unit_id})
    assert added.status_code == 201
    assert [u["unit_id"] for u in added.json()["units"]] == [unit_id]

    removed = client.delete(f"/api/applications/{application_token}/units/{unit_id}")
    assert removed.status_code == 200
    assert removed.json()["units"] == []


def test_the_same_apartment_cannot_be_added_twice(client, application_token, unit_ids) -> None:  # noqa: ANN001
    """Backed by the unique constraint on (application_id, unit_id)."""
    unit_id = unit_ids["vapaarahoitteinen"]
    client.post(f"/api/applications/{application_token}/units", json={"unit_id": unit_id})

    again = client.post(f"/api/applications/{application_token}/units", json={"unit_id": unit_id})

    assert again.status_code == 409


def test_a_sale_apartment_cannot_be_applied_for(client, application_token, unit_ids) -> None:  # noqa: ANN001
    response = client.post(
        f"/api/applications/{application_token}/units", json={"unit_id": unit_ids["myynti"]}
    )

    assert response.status_code == 400
    assert "Varaa näyttöaika" in response.json()["detail"]


def test_removing_an_apartment_that_is_not_in_the_basket_404s(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    response = client.delete(
        f"/api/applications/{application_token}/units/{unit_ids['vapaarahoitteinen']}"
    )

    assert response.status_code == 404


def test_the_form_grows_when_a_needs_assessed_apartment_is_added(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    """SPEC section 2.4, over the API the frontend actually calls."""
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["vapaarahoitteinen"]},
    )
    before = {
        f["field"]
        for f in client.get(f"/api/applications/{application_token}/required-fields").json()
    }

    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["tarveharkintainen"]},
    )
    after = client.get(f"/api/applications/{application_token}/required-fields").json()
    fields = {f["field"] for f in after}

    assert "assets" not in before
    assert fields - before == {"assets", "housing_need"}


def test_a_new_field_names_the_apartment_that_required_it(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["tarveharkintainen"]},
    )

    fields = client.get(f"/api/applications/{application_token}/required-fields").json()
    housing_need = next(f for f in fields if f["field"] == "housing_need")

    assert housing_need["label_fi"] == "asunnontarve"
    assert housing_need["required_by"]
    cause = housing_need["required_by"][0]
    assert cause["unit_id"] == unit_ids["tarveharkintainen"]
    assert cause["rule_id"].startswith("TARVE-")
    assert cause["rule_title_fi"]


def test_removing_the_apartment_removes_the_field_again(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    unit_id = unit_ids["tarveharkintainen"]
    client.post(f"/api/applications/{application_token}/units", json={"unit_id": unit_id})
    client.delete(f"/api/applications/{application_token}/units/{unit_id}")

    fields = {
        f["field"]
        for f in client.get(f"/api/applications/{application_token}/required-fields").json()
    }

    assert "housing_need" not in fields
    assert "assets" not in fields


def test_every_decision_carries_its_rule_message_and_evidence(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["vapaarahoitteinen"]},
    )

    decisions = client.get(f"/api/applications/{application_token}/decisions").json()

    assert len(decisions) == 1
    row = decisions[0]
    assert row["outcome"] in {"kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen"}
    assert row["deciding_rule_id"]
    assert row["message_fi"].strip()
    assert row["evidence"]
    for rule in row["rules"]:
        assert rule["rule_id"] and rule["message_fi"].strip() and rule["evidence"]


def test_an_empty_application_is_undecided_not_rejected(
    client, application_token, unit_ids
) -> None:  # noqa: ANN001
    """Nothing filled in yet: the answer is "we cannot decide", never "no"."""
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["tarveharkintainen"]},
    )

    decisions = client.get(f"/api/applications/{application_token}/decisions").json()

    assert decisions[0]["outcome"] == "puuttuvat_tiedot"


def test_one_basket_can_hold_different_outcomes(client, application_token, unit_ids) -> None:  # noqa: ANN001
    """Scenario 3 over the API: over the needs-assessed limit, fine for open stock."""
    client.put(
        f"/api/applications/{application_token}",
        json={
            "members": [
                {
                    "role": "paahakija",
                    "birth_year": 1988,
                    "gross_monthly_income_eur": "3250",
                    "assets_eur": "8000",
                }
            ],
            "housing_need": {"situation": "ahtaasti"},
            "deposit_acknowledged": True,
            "credit_default_flag": False,
        },
    )
    for key in ("vapaarahoitteinen", "tarveharkintainen"):
        client.post(f"/api/applications/{application_token}/units", json={"unit_id": unit_ids[key]})

    decisions = {
        d["housing_form"]: d
        for d in client.get(f"/api/applications/{application_token}/decisions").json()
    }

    assert decisions["vapaarahoitteinen"]["outcome"] == "kelpoinen"
    assert decisions["tarveharkintainen"]["outcome"] == "ei_kelpoinen"
    assert decisions["tarveharkintainen"]["deciding_rule_id"] == "TARVE-TULO-01"


def test_an_expired_application_resets_every_decision(
    client, application_token, unit_ids, engine
) -> None:  # noqa: ANN001
    """SPEC section 5: expiry is a request to confirm, not a rejection."""
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["vapaarahoitteinen"]},
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE applications SET created_at = now() - interval '4 months',"
                " expires_at = now() - interval '1 month' WHERE edit_token = :token"
            ),
            {"token": application_token},
        )

    body = client.get(f"/api/applications/{application_token}").json()
    decisions = client.get(f"/api/applications/{application_token}/decisions").json()

    assert body["expired"] is True
    assert decisions[0]["outcome"] == "puuttuvat_tiedot"
    assert decisions[0]["deciding_rule_id"] == "YLEIS-VANHENTUNUT-01"
    assert "muokkauslinkki" in decisions[0]["message_fi"]


def test_editing_records_what_was_decided_and_when(
    client, application_token, unit_ids, engine
) -> None:  # noqa: ANN001
    """The decisions table is the audit trail; reads always re-evaluate."""
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["vapaarahoitteinen"]},
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT rule_id, evidence_json FROM decisions ORDER BY id")
        ).all()

    assert rows
    assert all(rule_id and evidence for rule_id, evidence in rows)


def test_deleting_an_application_cascades(client, application_token, unit_ids, engine) -> None:  # noqa: ANN001
    """The cascade is declared in the schema; this proves it is actually there."""
    client.put(
        f"/api/applications/{application_token}",
        json={
            "members": [{"role": "paahakija", "birth_year": 1990}],
            "housing_need": {"situation": "ahtaasti"},
        },
    )
    client.post(
        f"/api/applications/{application_token}/units",
        json={"unit_id": unit_ids["vapaarahoitteinen"]},
    )

    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM applications WHERE edit_token = :token"),
            {"token": application_token},
        )
        remaining = {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            for table in ("household_members", "housing_need", "application_units", "decisions")
        }

    assert remaining == dict.fromkeys(remaining, 0)
