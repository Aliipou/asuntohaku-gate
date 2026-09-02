"""Request and response models.

Money is typed as ``Decimal`` and therefore serialises to a JSON *string*
("895.00"). That is deliberate: rents and asset limits must not go through a
float, and the frontend formats them for display anyway rather than doing
arithmetic on them.

Every response that carries a decision also carries the rule that produced it,
its Finnish message and its evidence — both raw and formatted — so a client
cannot render an outcome without the reason for it even by accident.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from api.texts import fi

OutcomeValue = Literal["kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen"]
HousingForm = Literal["vapaarahoitteinen", "lyhyt_korkotuki", "tarveharkintainen", "asumisoikeus"]
ListingType = Literal["vuokra", "myynti"]
Availability = Literal["vapaa", "vapautuu", "sopimuksella"]
MemberRole = Literal["paahakija", "toinen", "muu"]
NeedSituation = Literal["asunnoton", "irtisanottu", "ahtaasti", "ei_tarvetta"]


def jsonable(value: Any) -> Any:
    """Make a rule's evidence value safe for JSON without losing precision."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dt.datetime | dt.date):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value


class EvidenceItem(BaseModel):
    """One value that contributed to a decision, raw and ready to display."""

    avain: str
    arvo: Any
    teksti: str

    @classmethod
    def from_evidence(cls, evidence: Mapping[str, Any]) -> list[EvidenceItem]:
        return [
            cls(avain=key, arvo=jsonable(value), teksti=fi.evidence_value(key, value))
            for key, value in evidence.items()
        ]


class RuleOutcomeOut(BaseModel):
    rule_id: str
    rule_title_fi: str
    outcome: OutcomeValue
    outcome_label_fi: str
    message_fi: str
    evidence: list[EvidenceItem]


class DecisionOut(BaseModel):
    """One row on the decisions screen."""

    unit_id: int
    unit_label: str
    housing_form: HousingForm
    outcome: OutcomeValue
    outcome_label_fi: str
    #: The rule that produced the outcome. For a kelpoinen row every rule agreed,
    #: so clients should show `rules` rather than singling this one out.
    deciding_rule_id: str
    message_fi: str
    evidence: list[EvidenceItem]
    rules: list[RuleOutcomeOut]


class FieldCauseOut(BaseModel):
    """Which chosen apartment made the form ask for something."""

    unit_id: int
    unit_label: str
    rule_id: str
    rule_title_fi: str


class RequiredFieldOut(BaseModel):
    field: str
    label_fi: str
    required_by: list[FieldCauseOut]


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    property_name: str
    street: str
    postal_code: str
    city: str
    built_year: int
    housing_form: HousingForm
    housing_form_label_fi: str
    unit_number: str
    rooms: int
    floor: int
    area_m2: Decimal
    listing_type: ListingType
    rent_eur: Decimal | None
    price_eur: Decimal | None
    deposit_eur: Decimal | None
    availability: Availability
    available_from: dt.date | None


class UnitDetailOut(UnitOut):
    housing_form_explanation_fi: str
    description_fi: str
    description_en: str | None


class UnitSearchOut(BaseModel):
    total: int
    units: list[UnitOut]
    cached: bool = False


class MemberIn(BaseModel):
    role: MemberRole = "paahakija"
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    gross_monthly_income_eur: Decimal | None = Field(default=None, ge=0)
    assets_eur: Decimal | None = Field(default=None, ge=0)


class MemberOut(MemberIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class HousingNeedIn(BaseModel):
    situation: NeedSituation
    urgency_note: str | None = None


class ApplicationCreate(BaseModel):
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class ApplicationUpdate(BaseModel):
    """Every field optional: the form is filled in over several visits."""

    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    order_number: str | None = None
    deposit_acknowledged: bool | None = None
    credit_default_flag: bool | None = None
    members: list[MemberIn] | None = None
    housing_need: HousingNeedIn | None = None


class ApplicationUnitOut(BaseModel):
    unit_id: int
    unit_label: str
    housing_form: HousingForm
    preference_rank: int


class ApplicationOut(BaseModel):
    edit_token: str
    status: str
    created_at: dt.datetime
    expires_at: dt.datetime
    expired: bool
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    order_number: str | None
    deposit_acknowledged: bool | None
    credit_default_flag: bool | None
    members: list[MemberOut]
    housing_need: HousingNeedIn | None
    units: list[ApplicationUnitOut]


class AddUnitIn(BaseModel):
    unit_id: int
    preference_rank: int | None = Field(default=None, ge=1)


class ViewingOut(BaseModel):
    id: int
    unit_id: int
    starts_at: dt.datetime
    capacity: int
    booked: int
    seats_left: int


class BookingIn(BaseModel):
    edit_token: str


class BookingOut(BaseModel):
    id: int
    viewing_id: int
    created_at: dt.datetime


class OfferIn(BaseModel):
    contact_name: str = Field(min_length=1, max_length=160)
    contact_email: str = Field(min_length=3, max_length=254)
    amount_eur: Decimal = Field(gt=0)
    message: str | None = None


class OfferOut(BaseModel):
    id: int
    unit_id: int
    contact_name: str
    amount_eur: Decimal
    created_at: dt.datetime


class RankedApplicantOut(BaseModel):
    rank: int
    application_id: int
    contact_name: str | None
    rule_id: str
    message_fi: str
    evidence: list[EvidenceItem]
    eligibility: OutcomeValue
    eligibility_message_fi: str


class ApplicantRankingOut(BaseModel):
    unit_id: int
    unit_label: str
    housing_form: HousingForm
    #: Absent for housing forms that do not rank applicants against each other.
    ranking_rule_id: str | None
    ranking_basis_fi: str | None
    applicants: list[RankedApplicantOut]


class ErrorOut(BaseModel):
    detail: str
    message_fi: str
