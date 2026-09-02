"""Apartment search and detail, viewings and offers for one apartment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from api.app import cache
from api.app.db import get_session
from api.app.models import Contact, Offer, Property, Unit, Viewing, ViewingBooking
from api.app.schemas import (
    ContactOut,
    OfferIn,
    OfferOut,
    SortOrder,
    UnitDetailOut,
    UnitImageOut,
    UnitOut,
    UnitSearchOut,
    ViewingOut,
)
from api.app.snapshots import unit_label
from api.texts import fi

router = APIRouter(prefix="/api/units", tags=["units"])

SessionDep = Annotated[Session, Depends(get_session)]


def unit_to_out(unit: Unit) -> UnitOut:
    return UnitOut(
        id=unit.id,
        label=unit_label(unit),
        property_name=unit.property.name,
        street=unit.property.street,
        postal_code=unit.property.postal_code,
        city=unit.property.city,
        built_year=unit.property.built_year,
        housing_form=unit.property.housing_form,  # type: ignore[arg-type]
        housing_form_label_fi=fi.HOUSING_FORM_LABELS[unit.property.housing_form],
        unit_number=unit.unit_number,
        rooms=unit.rooms,
        floor=unit.floor,
        area_m2=unit.area_m2,
        listing_type=unit.listing_type,  # type: ignore[arg-type]
        rent_eur=unit.rent_eur,
        price_eur=unit.price_eur,
        deposit_eur=unit.deposit_eur,
        availability=unit.availability,  # type: ignore[arg-type]
        available_from=unit.available_from,
        maintenance_fee_eur=unit.maintenance_fee_eur,
        room_layout_fi=unit.room_layout_fi,
        dwelling_type=unit.dwelling_type,  # type: ignore[arg-type]
        has_lift=unit.has_lift,
        has_sauna=unit.has_sauna,
        has_balcony=unit.has_balcony,
        pets_allowed=unit.pets_allowed,
        accessible=unit.accessible,
        lat=unit.property.lat,
        lng=unit.property.lng,
        primary_image=_primary_image(unit),
    )


def _primary_image(unit: Unit) -> UnitImageOut | None:
    """The first photograph. A floor plan is not what a result row should lead with."""
    photos = [i for i in unit.images if i.kind == "valokuva"] or list(unit.images)
    if not photos:
        return None
    return UnitImageOut.model_validate(min(photos, key=lambda i: i.sort_order))


def _cache_key(params: Mapping[str, object]) -> str:
    payload = json.dumps(params, sort_keys=True, default=str)
    return "units:search:" + hashlib.sha256(payload.encode()).hexdigest()[:32]


@router.get("", response_model=UnitSearchOut)
def search_units(
    session: SessionDep,
    city: str | None = None,
    housing_form: Literal[
        "vapaarahoitteinen", "lyhyt_korkotuki", "tarveharkintainen", "asumisoikeus"
    ]
    | None = None,
    listing_type: Literal["vuokra", "myynti"] | None = None,
    availability: Literal["vapaa", "vapautuu", "sopimuksella"] | None = None,
    rooms_min: Annotated[int | None, Query(ge=1)] = None,
    rooms_max: Annotated[int | None, Query(ge=1)] = None,
    rent_min: Annotated[Decimal | None, Query(ge=0)] = None,
    rent_max: Annotated[Decimal | None, Query(ge=0)] = None,
    price_min: Annotated[Decimal | None, Query(ge=0)] = None,
    price_max: Annotated[Decimal | None, Query(ge=0)] = None,
    sort: SortOrder = "uusimmat",
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UnitSearchOut:
    """Both rental and sale stock in one index, filtered and cached for 60 seconds."""
    params = {
        "city": city,
        "housing_form": housing_form,
        "listing_type": listing_type,
        "availability": availability,
        "rooms_min": rooms_min,
        "rooms_max": rooms_max,
        "rent_min": rent_min,
        "rent_max": rent_max,
        "price_min": price_min,
        "price_max": price_max,
        "sort": sort,
        "limit": limit,
        "offset": offset,
    }
    key = _cache_key(params)
    cached = cache.get_json(key)
    if cached is not None:
        return UnitSearchOut(**cached, cached=True)

    query = (
        select(Unit)
        .join(Unit.property)
        .options(selectinload(Unit.property), selectinload(Unit.images))
    )
    if city:
        query = query.where(Property.city == city)
    if housing_form:
        query = query.where(Property.housing_form == housing_form)
    if listing_type:
        query = query.where(Unit.listing_type == listing_type)
    if availability:
        query = query.where(Unit.availability == availability)
    if rooms_min is not None:
        query = query.where(Unit.rooms >= rooms_min)
    if rooms_max is not None:
        query = query.where(Unit.rooms <= rooms_max)
    if rent_min is not None:
        query = query.where(Unit.rent_eur >= rent_min)
    if rent_max is not None:
        query = query.where(Unit.rent_eur <= rent_max)
    if price_min is not None:
        query = query.where(Unit.price_eur >= price_min)
    if price_max is not None:
        query = query.where(Unit.price_eur <= price_max)

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    units = session.scalars(query.order_by(*_ordering(sort)).limit(limit).offset(offset)).all()

    result = UnitSearchOut(total=total, units=[unit_to_out(u) for u in units])
    cache.set_json(key, result.model_dump(mode="json", exclude={"cached"}))
    return result


#: One apartment has either a rent or a price, never both, so "cheapest" has to
#: compare across the two rather than sorting a column that is null half the time.
def _price_expression() -> Any:
    return func.coalesce(Unit.rent_eur, Unit.price_eur)


def _ordering(sort: SortOrder) -> tuple[Any, ...]:
    """SQL ordering for the sort the UI offers.

    `uusimmat` falls back to insertion order: units carry no publication date,
    and inventing one in the ORDER BY would be a claim the data does not make.
    """
    tiebreak = (Property.city, Property.street, Unit.unit_number)
    if sort == "halvin":
        return (_price_expression().asc(), *tiebreak)
    if sort == "kallein":
        return (_price_expression().desc(), *tiebreak)
    if sort == "suurin":
        return (Unit.area_m2.desc(), *tiebreak)
    return (Unit.id.desc(),)


def _get_unit(session: Session, unit_id: int) -> Unit:
    unit = session.scalars(
        select(Unit)
        .where(Unit.id == unit_id)
        .options(selectinload(Unit.property), selectinload(Unit.images))
    ).one_or_none()
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_found())
    return unit


@router.get("/{unit_id}", response_model=UnitDetailOut)
def get_unit(unit_id: int, session: SessionDep) -> UnitDetailOut:
    unit = _get_unit(session, unit_id)
    base = unit_to_out(unit)
    contact = session.scalars(
        select(Contact).where(Contact.property_id == unit.property_id).order_by(Contact.id).limit(1)
    ).one_or_none()
    return UnitDetailOut(
        **base.model_dump(exclude={"primary_image"}),
        primary_image=base.primary_image,
        housing_form_explanation_fi=fi.HOUSING_FORM_EXPLANATIONS[unit.property.housing_form],
        description_fi=unit.description_fi,
        description_en=unit.description_en,
        images=[UnitImageOut.model_validate(i) for i in unit.images],
        contact=ContactOut.model_validate(contact) if contact else None,
    )


@router.get("/{unit_id}/viewings", response_model=list[ViewingOut])
def list_viewings(unit_id: int, session: SessionDep) -> list[ViewingOut]:
    _get_unit(session, unit_id)
    rows = session.execute(
        select(Viewing, func.count(ViewingBooking.id))
        .outerjoin(ViewingBooking, ViewingBooking.viewing_id == Viewing.id)
        .where(Viewing.unit_id == unit_id)
        .group_by(Viewing.id)
        .order_by(Viewing.starts_at)
    ).all()
    return [
        ViewingOut(
            id=viewing.id,
            unit_id=viewing.unit_id,
            starts_at=viewing.starts_at,
            capacity=viewing.capacity,
            booked=booked,
            seats_left=max(viewing.capacity - booked, 0),
        )
        for viewing, booked in rows
    ]


@router.post("/{unit_id}/offers", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def create_offer(unit_id: int, payload: OfferIn, session: SessionDep) -> OfferOut:
    """Offers are for sale stock. Rental apartments are applied for, not bid on."""
    unit = _get_unit(session, unit_id)
    if unit.listing_type != "myynti":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=fi.offers_only_for_sale_units())

    offer = Offer(
        unit_id=unit.id,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        amount_eur=payload.amount_eur,
        message=payload.message,
        created_at=dt.datetime.now(dt.UTC),
    )
    session.add(offer)
    session.flush()
    return OfferOut(
        id=offer.id,
        unit_id=offer.unit_id,
        contact_name=offer.contact_name,
        amount_eur=offer.amount_eur,
        created_at=offer.created_at,
    )
