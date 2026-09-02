"""Booking a viewing.

Capacity is enforced by the database trigger, not by a count in Python. Two
concurrent bookings for the last seat serialise on the viewing's row lock, and
the loser gets a 409 rather than a seat that does not exist.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import errors as pg_errors
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from api.app.db import get_session
from api.app.models import Application, Viewing, ViewingBooking
from api.app.schemas import BookingIn, BookingOut
from api.texts import fi

router = APIRouter(prefix="/api/viewings", tags=["viewings"])

SessionDep = Annotated[Session, Depends(get_session)]

#: SQLSTATE raised by the capacity trigger in migration 0001.
VIEWING_FULL_SQLSTATE = "P0001"


@router.post(
    "/{viewing_id}/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED
)
def create_booking(viewing_id: int, payload: BookingIn, session: SessionDep) -> BookingOut:
    viewing = session.get(Viewing, viewing_id)
    if viewing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.viewing_not_found())

    try:
        token = uuid.UUID(payload.edit_token)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.application_not_found()) from None
    application = session.scalars(
        select(Application).where(Application.edit_token == token)
    ).one_or_none()
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.application_not_found())

    booking = ViewingBooking(
        viewing_id=viewing.id,
        application_id=application.id,
        created_at=dt.datetime.now(dt.UTC),
    )
    session.add(booking)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=fi.already_booked()) from exc
    except DBAPIError as exc:
        session.rollback()
        if _is_viewing_full(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=fi.viewing_full()) from exc
        raise

    return BookingOut(id=booking.id, viewing_id=booking.viewing_id, created_at=booking.created_at)


def _is_viewing_full(exc: DBAPIError) -> bool:
    original = getattr(exc, "orig", None)
    if isinstance(original, pg_errors.RaiseException):
        return getattr(original, "sqlstate", None) == VIEWING_FULL_SQLSTATE
    return "VIEWING_FULL" in str(original)
