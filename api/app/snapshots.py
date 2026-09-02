"""Mapping ORM rows to the frozen snapshots the rule engine consumes.

This is the boundary. Everything below it can query and mutate; everything above
it is pure. The evaluation moment is supplied by the caller and travels on the
snapshot, so no rule has to be trusted not to look at a clock.
"""

from __future__ import annotations

import datetime as dt

from api.app.models import Application, Unit
from api.rules.types import ApplicationSnapshot, MemberSnapshot, UnitSnapshot


def unit_label(unit: Unit) -> str:
    """What the applicant sees an apartment called, in decisions and in the form."""
    return f"{unit.property.street} {unit.unit_number}, {unit.property.city}"


def unit_snapshot(unit: Unit) -> UnitSnapshot:
    return UnitSnapshot(
        id=unit.id,
        label=unit_label(unit),
        city=unit.property.city,
        housing_form=unit.property.housing_form,  # type: ignore[arg-type]
        listing_type=unit.listing_type,  # type: ignore[arg-type]
        rooms=unit.rooms,
        area_m2=unit.area_m2,
        rent_eur=unit.rent_eur,
        price_eur=unit.price_eur,
        deposit_eur=unit.deposit_eur,
    )


def application_snapshot(
    application: Application, *, evaluated_at: dt.datetime
) -> ApplicationSnapshot:
    need = application.housing_need
    return ApplicationSnapshot(
        id=application.id,
        evaluated_at=evaluated_at,
        created_at=application.created_at,
        expires_at=application.expires_at,
        members=tuple(
            MemberSnapshot(
                role=member.role,  # type: ignore[arg-type]
                birth_year=member.birth_year,
                gross_monthly_income_eur=member.gross_monthly_income_eur,
                assets_eur=member.assets_eur,
            )
            for member in application.members
        ),
        housing_need=need.situation if need else None,  # type: ignore[arg-type]
        urgency_note=need.urgency_note if need else None,
        order_number=application.order_number,
        deposit_acknowledged=application.deposit_acknowledged,
        credit_default_flag=application.credit_default_flag,
    )
