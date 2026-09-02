"""Viewing bookings, including the concurrency test SPEC section 9 asks for."""

from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from tests.api.conftest import requires_db

pytestmark = requires_db


def _make_viewing(engine: Engine, unit_id: int, capacity: int) -> int:
    with engine.begin() as connection:
        return connection.execute(
            text(
                "INSERT INTO viewings (unit_id, starts_at, capacity)"
                " VALUES (:unit_id, now() + interval '7 days', :capacity) RETURNING id"
            ),
            {"unit_id": unit_id, "capacity": capacity},
        ).scalar_one()


def _make_application(engine: Engine) -> tuple[int, str]:
    with engine.begin() as connection:
        return connection.execute(
            text(
                "INSERT INTO applications (edit_token, status, created_at, expires_at)"
                " VALUES (gen_random_uuid(), 'luonnos', now(), now() + interval '3 months')"
                " RETURNING id, edit_token::text"
            )
        ).one()


def test_viewings_are_listed_with_seats_left(client, unit_ids, engine) -> None:  # noqa: ANN001
    unit_id = unit_ids["myynti"]
    _make_viewing(engine, unit_id, capacity=3)

    body = client.get(f"/api/units/{unit_id}/viewings").json()

    assert len(body) == 1
    assert body[0]["capacity"] == 3
    assert body[0]["booked"] == 0
    assert body[0]["seats_left"] == 3


def test_booking_a_seat(client, unit_ids, engine, application_token) -> None:  # noqa: ANN001
    viewing_id = _make_viewing(engine, unit_ids["myynti"], capacity=2)

    response = client.post(
        f"/api/viewings/{viewing_id}/bookings", json={"edit_token": application_token}
    )

    assert response.status_code == 201
    listed = client.get(f"/api/units/{unit_ids['myynti']}/viewings").json()[0]
    assert listed["booked"] == 1
    assert listed["seats_left"] == 1


def test_the_same_application_cannot_book_twice(
    client, unit_ids, engine, application_token
) -> None:  # noqa: ANN001
    """Backed by the unique constraint on (viewing_id, application_id)."""
    viewing_id = _make_viewing(engine, unit_ids["myynti"], capacity=5)
    client.post(f"/api/viewings/{viewing_id}/bookings", json={"edit_token": application_token})

    again = client.post(
        f"/api/viewings/{viewing_id}/bookings", json={"edit_token": application_token}
    )

    assert again.status_code == 409
    assert "jo varannut" in again.json()["detail"]


def test_a_full_viewing_is_refused(client, unit_ids, engine) -> None:  # noqa: ANN001
    viewing_id = _make_viewing(engine, unit_ids["myynti"], capacity=1)
    _first_id, first_token = _make_application(engine)
    _second_id, second_token = _make_application(engine)

    assert (
        client.post(
            f"/api/viewings/{viewing_id}/bookings", json={"edit_token": first_token}
        ).status_code
        == 201
    )
    refused = client.post(f"/api/viewings/{viewing_id}/bookings", json={"edit_token": second_token})

    assert refused.status_code == 409
    assert "täynnä" in refused.json()["detail"]


def test_booking_an_unknown_viewing_or_application_404s(
    client, engine, unit_ids, application_token
) -> None:  # noqa: ANN001
    viewing_id = _make_viewing(engine, unit_ids["myynti"], capacity=1)

    no_viewing = client.post(
        "/api/viewings/999999/bookings", json={"edit_token": application_token}
    )
    no_application = client.post(
        f"/api/viewings/{viewing_id}/bookings",
        json={"edit_token": "2b1f8f0e-0000-4000-8000-000000000000"},
    )

    assert no_viewing.status_code == 404
    assert no_application.status_code == 404


@pytest.mark.parametrize("capacity", [1, 3])
def test_concurrent_bookings_cannot_exceed_capacity(
    engine, unit_ids, seeded, capacity: int
) -> None:  # noqa: ANN001
    """SPEC section 9: prove the capacity guard under real concurrency.

    Eight connections race for `capacity` seats. The trigger takes a row lock on
    the viewing before counting, so the losers raise instead of overbooking. If
    the guard were a count in Python this test would overbook.
    """
    attempts = 8
    viewing_id = _make_viewing(engine, unit_ids["myynti"], capacity=capacity)
    application_ids = [_make_application(engine)[0] for _ in range(attempts)]
    now = dt.datetime.now(dt.UTC)

    def book(application_id: int) -> bool:
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO viewing_bookings (viewing_id, application_id, created_at)"
                        " VALUES (:viewing_id, :application_id, :created_at)"
                    ),
                    {
                        "viewing_id": viewing_id,
                        "application_id": application_id,
                        "created_at": now,
                    },
                )
            return True
        except DBAPIError:
            return False

    with ThreadPoolExecutor(max_workers=attempts) as pool:
        results = list(pool.map(book, application_ids))

    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT count(*) FROM viewing_bookings WHERE viewing_id = :id"),
            {"id": viewing_id},
        ).scalar_one()

    assert sum(results) == capacity
    assert stored == capacity
