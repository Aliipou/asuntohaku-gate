"""Builders for rule tests.

Every test states only the fields it cares about; the builders fill in a
household and an apartment that are otherwise unremarkable, so a table row reads
as the case it is testing rather than as a wall of setup.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from api.rules.types import ApplicationSnapshot, MemberSnapshot, UnitSnapshot
from seeds.limits import DEMO_LIMITS

LIMITS = DEMO_LIMITS

#: Fixed evaluation moment. Nothing in the engine reads a clock, so tests do not
#: need to freeze one.
NOW = dt.datetime(2026, 9, 2, 12, 0, tzinfo=dt.UTC)


def eur(amount: str | int | None) -> Decimal | None:
    return None if amount is None else Decimal(str(amount))


def member(
    *,
    role: str = "paahakija",
    birth_year: int | None = 1990,
    income: str | int | None = 2500,
    assets: str | int | None = 5000,
) -> MemberSnapshot:
    return MemberSnapshot(
        role=role,  # type: ignore[arg-type]
        birth_year=birth_year,
        gross_monthly_income_eur=eur(income),
        assets_eur=eur(assets),
    )


def application(
    *,
    id: int = 1,
    members: tuple[MemberSnapshot, ...] | None = None,
    housing_need: str | None = "ahtaasti",
    urgency_note: str | None = None,
    order_number: str | None = "123456",
    deposit_acknowledged: bool | None = True,
    credit_default_flag: bool | None = False,
    created_at: dt.datetime | None = None,
    expires_at: dt.datetime | None = None,
    evaluated_at: dt.datetime = NOW,
) -> ApplicationSnapshot:
    created = created_at if created_at is not None else NOW - dt.timedelta(days=7)
    return ApplicationSnapshot(
        id=id,
        evaluated_at=evaluated_at,
        created_at=created,
        expires_at=expires_at if expires_at is not None else created + dt.timedelta(days=92),
        members=members if members is not None else (member(),),
        housing_need=housing_need,  # type: ignore[arg-type]
        urgency_note=urgency_note,
        order_number=order_number,
        deposit_acknowledged=deposit_acknowledged,
        credit_default_flag=credit_default_flag,
    )


def unit(
    *,
    id: int = 100,
    label: str = "Kotikatu 3 A 12",
    city: str = "Helsinki",
    housing_form: str = "vapaarahoitteinen",
    listing_type: str = "vuokra",
    rooms: int = 2,
    area_m2: str | int = 54,
    rent: str | int | None = 900,
    price: str | int | None = None,
    deposit: str | int | None = 900,
) -> UnitSnapshot:
    return UnitSnapshot(
        id=id,
        label=label,
        city=city,
        housing_form=housing_form,  # type: ignore[arg-type]
        listing_type=listing_type,  # type: ignore[arg-type]
        rooms=rooms,
        area_m2=Decimal(str(area_m2)),
        rent_eur=eur(rent),
        price_eur=eur(price),
        deposit_eur=eur(deposit),
    )
