"""The endpoints the portal-style search and listing pages need.

City autocomplete, similar listings, and the two things a property portal lets
an anonymous visitor keep: favourites and saved searches.

There is still no login. Both lists key on an opaque value the browser
generates and sends. It authenticates nobody and grants access to nothing but
its own list — which is exactly why it must never be used for anything else.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from api.app.db import get_session
from api.app.models import Favourite, Property, SavedSearch, Unit
from api.app.routers.units import unit_to_out
from api.app.schemas import CityOut, FavouriteIn, SavedSearchIn, SavedSearchOut, UnitOut
from api.texts import fi

router = APIRouter(prefix="/api", tags=["portal"])

SessionDep = Annotated[Session, Depends(get_session)]

#: How far a "similar" apartment may differ before it stops being comparable.
SIMILAR_AREA_TOLERANCE = Decimal("0.35")
SIMILAR_PRICE_TOLERANCE = Decimal("0.35")
SIMILAR_LIMIT = 4


@router.get("/cities", response_model=list[CityOut])
def list_cities(session: SessionDep) -> list[CityOut]:
    """Cities that actually have stock, with counts. Feeds the search autocomplete."""
    rows = session.execute(
        select(Property.city, func.count(Unit.id))
        .join(Unit, Unit.property_id == Property.id)
        .group_by(Property.city)
        .order_by(Property.city)
    ).all()
    return [CityOut(city=city, units=count) for city, count in rows]


@router.get("/units/{unit_id}/similar", response_model=list[UnitOut])
def similar_units(unit_id: int, session: SessionDep) -> list[UnitOut]:
    """Vastaavia asuntoja: same city and listing type, comparable size and price."""
    unit = session.scalars(
        select(Unit).where(Unit.id == unit_id).options(selectinload(Unit.property))
    ).one_or_none()
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_found())

    price = unit.rent_eur if unit.listing_type == "vuokra" else unit.price_eur
    price_column = Unit.rent_eur if unit.listing_type == "vuokra" else Unit.price_eur

    query = (
        select(Unit)
        .join(Unit.property)
        .options(selectinload(Unit.property), selectinload(Unit.images))
        .where(
            Unit.id != unit.id,
            Property.city == unit.property.city,
            Unit.listing_type == unit.listing_type,
            Unit.area_m2.between(
                unit.area_m2 * (1 - SIMILAR_AREA_TOLERANCE),
                unit.area_m2 * (1 + SIMILAR_AREA_TOLERANCE),
            ),
        )
    )
    if price is not None:
        query = query.where(
            price_column.between(
                price * (1 - SIMILAR_PRICE_TOLERANCE), price * (1 + SIMILAR_PRICE_TOLERANCE)
            )
        )

    units = session.scalars(
        query.order_by(func.abs(Unit.area_m2 - unit.area_m2)).limit(SIMILAR_LIMIT)
    ).all()
    return [unit_to_out(u) for u in units]


@router.get("/favourites", response_model=list[UnitOut])
def list_favourites(
    session: SessionDep, session_key: Annotated[str, Query(min_length=8, max_length=64)]
) -> list[UnitOut]:
    units = session.scalars(
        select(Unit)
        .join(Favourite, Favourite.unit_id == Unit.id)
        .options(selectinload(Unit.property), selectinload(Unit.images))
        .where(Favourite.session_key == session_key)
        .order_by(Favourite.created_at.desc())
    ).all()
    return [unit_to_out(u) for u in units]


@router.post("/favourites", response_model=list[UnitOut], status_code=status.HTTP_201_CREATED)
def add_favourite(payload: FavouriteIn, session: SessionDep) -> list[UnitOut]:
    if session.get(Unit, payload.unit_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_found())
    session.add(
        Favourite(
            session_key=payload.session_key,
            unit_id=payload.unit_id,
            created_at=dt.datetime.now(dt.UTC),
        )
    )
    try:
        session.flush()
    except IntegrityError:
        # Already saved. Favouriting twice is not an error the visitor should see.
        session.rollback()
    return list_favourites(session, payload.session_key)


@router.delete("/favourites/{unit_id}", response_model=list[UnitOut])
def remove_favourite(
    unit_id: int,
    session: SessionDep,
    session_key: Annotated[str, Query(min_length=8, max_length=64)],
) -> list[UnitOut]:
    session.execute(
        delete(Favourite).where(Favourite.session_key == session_key, Favourite.unit_id == unit_id)
    )
    session.flush()
    return list_favourites(session, session_key)


@router.get("/saved-searches", response_model=list[SavedSearchOut])
def list_saved_searches(
    session: SessionDep, session_key: Annotated[str, Query(min_length=8, max_length=64)]
) -> list[SavedSearchOut]:
    rows = session.scalars(
        select(SavedSearch)
        .where(SavedSearch.session_key == session_key)
        .order_by(SavedSearch.created_at.desc())
    ).all()
    return [
        SavedSearchOut(id=r.id, name=r.name, query=dict(r.query_json), created_at=r.created_at)
        for r in rows
    ]


@router.post("/saved-searches", response_model=SavedSearchOut, status_code=status.HTTP_201_CREATED)
def save_search(payload: SavedSearchIn, session: SessionDep) -> SavedSearchOut:
    """Stores the filter state the search page already encodes in its URL."""
    saved = SavedSearch(
        session_key=payload.session_key,
        name=payload.name,
        query_json=payload.query,
        created_at=dt.datetime.now(dt.UTC),
    )
    session.add(saved)
    session.flush()
    return SavedSearchOut(
        id=saved.id, name=saved.name, query=dict(saved.query_json), created_at=saved.created_at
    )
