"""The application: create, edit, choose apartments, and read the decisions.

There is no login. An application is reached by an unguessable edit token, which
is the whole access-control story and is stated as such in the README.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.app import cache, decisions
from api.app.dates import expiry_for
from api.app.db import get_session
from api.app.models import Application, ApplicationUnit, HouseholdMember, HousingNeed, Unit
from api.app.schemas import (
    AddUnitIn,
    ApplicationCreate,
    ApplicationOut,
    ApplicationUnitOut,
    ApplicationUpdate,
    DecisionOut,
    FieldCauseOut,
    HousingNeedIn,
    MemberOut,
    RequiredFieldOut,
)
from api.app.snapshots import unit_label, unit_snapshot
from api.rules.engine import required_fields
from api.texts import fi
from seeds.limits import DEMO_LIMITS

router = APIRouter(prefix="/api/applications", tags=["applications"])

SessionDep = Annotated[Session, Depends(get_session)]

# Transport limits, not eligibility thresholds: how often one edit token may
# write, so a script cannot hammer the API. Policy thresholds live only in
# seeds/limits.py.
EDIT_RATE_LIMIT = 60
EDIT_RATE_WINDOW_SECONDS = 60


def _now() -> dt.datetime:
    """The one place the API reads a clock. Everything downstream is given it."""
    return dt.datetime.now(dt.UTC)


def _load(session: Session, token: str) -> Application:
    try:
        parsed = uuid.UUID(token)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.application_not_found()) from None
    application = session.scalars(
        select(Application)
        .where(Application.edit_token == parsed)
        .options(
            selectinload(Application.members),
            selectinload(Application.housing_need),
            selectinload(Application.units)
            .selectinload(ApplicationUnit.unit)
            .selectinload(Unit.property),
        )
    ).one_or_none()
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.application_not_found())
    return application


def _throttle(token: str) -> None:
    if cache.hit_rate_limit(f"apply:edit:{token}", EDIT_RATE_LIMIT, EDIT_RATE_WINDOW_SECONDS):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=fi.too_many_requests())


def _to_out(application: Application, now: dt.datetime) -> ApplicationOut:
    need = application.housing_need
    return ApplicationOut(
        edit_token=str(application.edit_token),
        status=application.status,
        created_at=application.created_at,
        expires_at=application.expires_at,
        expired=now > application.expires_at,
        contact_name=application.contact_name,
        contact_email=application.contact_email,
        contact_phone=application.contact_phone,
        order_number=application.order_number,
        deposit_acknowledged=application.deposit_acknowledged,
        credit_default_flag=application.credit_default_flag,
        members=[MemberOut.model_validate(m) for m in application.members],
        housing_need=(
            HousingNeedIn(situation=need.situation, urgency_note=need.urgency_note)  # type: ignore[arg-type]
            if need
            else None
        ),
        units=[
            ApplicationUnitOut(
                unit_id=au.unit_id,
                unit_label=unit_label(au.unit),
                housing_form=au.unit.property.housing_form,  # type: ignore[arg-type]
                preference_rank=au.preference_rank,
            )
            for au in sorted(application.units, key=lambda a: (a.preference_rank, a.id))
        ],
    )


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, session: SessionDep) -> ApplicationOut:
    now = _now()
    application = Application(
        edit_token=uuid.uuid4(),
        status="luonnos",
        created_at=now,
        expires_at=expiry_for(now, DEMO_LIMITS.application_validity_months),
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )
    session.add(application)
    session.flush()
    return _to_out(application, now)


@router.get("/{token}", response_model=ApplicationOut)
def get_application(token: str, session: SessionDep) -> ApplicationOut:
    return _to_out(_load(session, token), _now())


@router.put("/{token}", response_model=ApplicationOut)
def update_application(
    token: str, payload: ApplicationUpdate, session: SessionDep
) -> ApplicationOut:
    _throttle(token)
    application = _load(session, token)
    now = _now()

    for field in ("contact_name", "contact_email", "contact_phone", "order_number"):
        value = getattr(payload, field)
        if value is not None:
            setattr(application, field, value)
    if payload.deposit_acknowledged is not None:
        application.deposit_acknowledged = payload.deposit_acknowledged
    if payload.credit_default_flag is not None:
        application.credit_default_flag = payload.credit_default_flag

    if payload.members is not None:
        # The household is replaced wholesale: the form edits it as one section,
        # and diffing rows would only invent identity the form does not have.
        application.members.clear()
        session.flush()
        for member in payload.members:
            application.members.append(
                HouseholdMember(
                    role=member.role,
                    birth_year=member.birth_year,
                    gross_monthly_income_eur=member.gross_monthly_income_eur,
                    assets_eur=member.assets_eur,
                )
            )

    if payload.housing_need is not None:
        if application.housing_need is None:
            application.housing_need = HousingNeed(
                situation=payload.housing_need.situation,
                urgency_note=payload.housing_need.urgency_note,
            )
        else:
            application.housing_need.situation = payload.housing_need.situation
            application.housing_need.urgency_note = payload.housing_need.urgency_note

    session.flush()
    decisions.record(session, decisions.evaluate(session, application, DEMO_LIMITS, now), now)
    session.flush()
    session.refresh(application)
    return _to_out(application, now)


@router.post("/{token}/units", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def add_unit(token: str, payload: AddUnitIn, session: SessionDep) -> ApplicationOut:
    _throttle(token)
    application = _load(session, token)
    now = _now()

    unit = session.scalars(
        select(Unit).where(Unit.id == payload.unit_id).options(selectinload(Unit.property))
    ).one_or_none()
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_found())
    if unit.listing_type != "vuokra":
        # Sale stock is bid on, not applied for. Letting one into a basket would
        # send it to rules that have no rent to work with.
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=fi.sale_unit_cannot_be_applied_for()
        )
    if any(au.unit_id == unit.id for au in application.units):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=fi.unit_already_in_application())

    rank = payload.preference_rank or (
        max((au.preference_rank for au in application.units), default=0) + 1
    )
    application.units.append(ApplicationUnit(unit_id=unit.id, preference_rank=rank))
    session.flush()
    decisions.record(session, decisions.evaluate(session, application, DEMO_LIMITS, now), now)
    session.flush()
    session.refresh(application)
    return _to_out(application, now)


@router.delete("/{token}/units/{unit_id}", response_model=ApplicationOut)
def remove_unit(token: str, unit_id: int, session: SessionDep) -> ApplicationOut:
    _throttle(token)
    application = _load(session, token)
    now = _now()

    chosen = next((au for au in application.units if au.unit_id == unit_id), None)
    if chosen is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_in_application())

    application.units.remove(chosen)
    session.flush()
    session.refresh(application)
    return _to_out(application, now)


@router.get("/{token}/required-fields", response_model=list[RequiredFieldOut])
def get_required_fields(token: str, session: SessionDep) -> list[RequiredFieldOut]:
    """What the form must ask for, given the apartments currently in the basket.

    The union of the `requires` metadata of every rule that applies. The frontend
    renders this; it does not keep a copy of the list.
    """
    application = _load(session, token)
    units = [unit_snapshot(au.unit) for au in application.units]
    return [
        RequiredFieldOut(
            field=field,
            label_fi=fi.REQUIRED_FIELD_LABELS[field],
            required_by=[
                FieldCauseOut(
                    unit_id=cause.unit_id,
                    unit_label=cause.unit_label,
                    rule_id=cause.rule_id,
                    rule_title_fi=cause.rule_title_fi,
                )
                for cause in causes
            ],
        )
        for field, causes in required_fields(units).items()
    ]


@router.get("/{token}/decisions", response_model=list[DecisionOut])
def get_decisions(token: str, session: SessionDep) -> list[DecisionOut]:
    """Re-evaluated on every read, so an application that expired in the meantime
    says so rather than serving a stored answer that is no longer true."""
    application = _load(session, token)
    now = _now()
    return [
        decisions.to_out(unit, decision)
        for _au, unit, decision in decisions.evaluate(session, application, DEMO_LIMITS, now)
    ]
