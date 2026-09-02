"""SQLAlchemy models.

Table and column names are English; every value that reaches a user is Finnish.
The constraints that matter for correctness are declared here so they end up in
the schema itself, not only in application code (SPEC section 4).
"""

from __future__ import annotations

import datetime as dt
import decimal
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

HOUSING_FORMS = ("vapaarahoitteinen", "lyhyt_korkotuki", "tarveharkintainen", "asumisoikeus")
LISTING_TYPES = ("vuokra", "myynti")
AVAILABILITIES = ("vapaa", "vapautuu", "sopimuksella")
APPLICATION_STATUSES = ("luonnos", "lahetetty", "vanhentunut")
MEMBER_ROLES = ("paahakija", "toinen", "muu")
NEED_SITUATIONS = ("asunnoton", "irtisanottu", "ahtaasti", "ei_tarvetta")
OUTCOMES = ("kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen")


def _enum(*values: str, name: str) -> Enum:
    """VARCHAR + CHECK rather than a native PostgreSQL enum type.

    The schema guarantee is the same and migrations that add a value later stay
    ordinary ALTERs instead of enum-type surgery.
    """
    return Enum(*values, name=name, native_enum=False, create_constraint=True)


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    street: Mapped[str] = mapped_column(String(160), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    housing_form: Mapped[str] = mapped_column(
        _enum(*HOUSING_FORMS, name="housing_form"), nullable=False
    )
    built_year: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[decimal.Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    lng: Mapped[decimal.Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    units: Mapped[list[Unit]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        # A rental unit carries rent and no price; a sale unit carries price and
        # no rent. SPEC section 4 asks for this as a check constraint.
        CheckConstraint(
            "(listing_type = 'vuokra' AND rent_eur IS NOT NULL AND price_eur IS NULL)"
            " OR (listing_type = 'myynti' AND price_eur IS NOT NULL AND rent_eur IS NULL)",
            name="ck_units_listing_price",
        ),
        CheckConstraint("area_m2 > 0", name="ck_units_area_positive"),
        CheckConstraint("rooms > 0", name="ck_units_rooms_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    area_m2: Mapped[decimal.Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    listing_type: Mapped[str] = mapped_column(
        _enum(*LISTING_TYPES, name="listing_type"), nullable=False
    )
    rent_eur: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2))
    price_eur: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2))
    deposit_eur: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2))
    availability: Mapped[str] = mapped_column(
        _enum(*AVAILABILITIES, name="availability"), nullable=False
    )
    available_from: Mapped[dt.date | None] = mapped_column(Date)
    description_fi: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[str | None] = mapped_column(Text)

    property: Mapped[Property] = relationship(back_populates="units")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    edit_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(
        _enum(*APPLICATION_STATUSES, name="application_status"),
        nullable=False,
        default="luonnos",
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # created_at plus the validity period from seeds/limits.py, written at insert
    # time by the caller. Nothing in the rule engine reads a clock.
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    contact_email: Mapped[str | None] = mapped_column(String(254))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    order_number: Mapped[str | None] = mapped_column(String(20))
    # Needed by VAPAA-VAKUUS-01 and VAPAA-LUOTTO-01. NULL means the applicant has
    # not answered yet, which is puuttuvat_tiedot and never a rejection.
    deposit_acknowledged: Mapped[bool | None] = mapped_column(Boolean)
    credit_default_flag: Mapped[bool | None] = mapped_column(Boolean)

    members: Mapped[list[HouseholdMember]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    housing_need: Mapped[HousingNeed | None] = relationship(
        back_populates="application", cascade="all, delete-orphan", uselist=False
    )
    units: Mapped[list[ApplicationUnit]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(_enum(*MEMBER_ROLES, name="member_role"), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    gross_monthly_income_eur: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 2))
    assets_eur: Mapped[decimal.Decimal | None] = mapped_column(Numeric(12, 2))

    application: Mapped[Application] = relationship(back_populates="members")


class HousingNeed(Base):
    __tablename__ = "housing_need"

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), primary_key=True
    )
    situation: Mapped[str] = mapped_column(
        _enum(*NEED_SITUATIONS, name="need_situation"), nullable=False
    )
    urgency_note: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="housing_need")


class ApplicationUnit(Base):
    __tablename__ = "application_units"
    __table_args__ = (UniqueConstraint("application_id", "unit_id", name="uq_application_units"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    preference_rank: Mapped[int] = mapped_column(Integer, nullable=False)

    application: Mapped[Application] = relationship(back_populates="units")
    unit: Mapped[Unit] = relationship()
    decisions: Mapped[list[Decision]] = relationship(
        back_populates="application_unit", cascade="all, delete-orphan"
    )


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        # The section 2.1 invariant, held in the schema as well as in the Outcome
        # type: no stored decision without a rule, a message and evidence.
        CheckConstraint("length(rule_id) > 0", name="ck_decisions_rule_id"),
        CheckConstraint("length(message_fi) > 0", name="ck_decisions_message"),
        CheckConstraint("evidence_json <> '{}'::jsonb", name="ck_decisions_evidence"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_unit_id: Mapped[int] = mapped_column(
        ForeignKey("application_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(_enum(*OUTCOMES, name="outcome"), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(40), nullable=False)
    message_fi: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    decided_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application_unit: Mapped[ApplicationUnit] = relationship(back_populates="decisions")


class Viewing(Base):
    __tablename__ = "viewings"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_viewings_capacity_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    starts_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)


class ViewingBooking(Base):
    __tablename__ = "viewing_bookings"
    __table_args__ = (UniqueConstraint("viewing_id", "application_id", name="uq_viewing_bookings"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    viewing_id: Mapped[int] = mapped_column(
        ForeignKey("viewings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (CheckConstraint("amount_eur > 0", name="ck_offers_amount_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
    amount_eur: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
