"""Types the rule engine is built on.

Two things are load-bearing here:

* ``Outcome`` cannot be constructed without a rule id, a Finnish message and
  non-empty evidence (SPEC section 2.1). There is no default and no bypass, so a
  rule that cannot say what decided it fails loudly instead of shipping a bare
  yes or no.
* The snapshots are frozen and self-contained. A rule receives everything it is
  allowed to know as an argument, including the moment of evaluation, so no rule
  needs a clock, a session or a query (SPEC section 2.3).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Literal, Self

OutcomeValue = Literal["kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen"]

#: Ordered worst-first. Used when several rules decide one apartment: the
#: apartment shows the most blocking outcome, and the rule that produced it.
OUTCOME_PRECEDENCE: tuple[OutcomeValue, ...] = (
    "ei_kelpoinen",
    "puuttuvat_tiedot",
    "kelpoinen",
)

#: The vocabulary of adaptive form fields. A rule's ``requires`` is drawn from
#: this set, and the union over the basket is what the form asks for.
RequiredField = Literal[
    "household_income",
    "assets",
    "housing_need",
    "order_number",
    "deposit_acknowledged",
    "credit_record",
    "household_size",
]


def _freeze(evidence: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(evidence))


@dataclass(frozen=True, slots=True)
class Outcome:
    """The result of one rule applied to one apartment.

    Every field is mandatory by construction. ``evidence`` holds the values that
    decided it, so the applicant can be shown the number that produced the
    answer rather than only the answer.
    """

    outcome: OutcomeValue
    rule_id: str
    message_fi: str
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOME_PRECEDENCE:
            raise ValueError(f"unknown outcome {self.outcome!r}")
        if not self.rule_id.strip():
            raise ValueError("outcome without a rule id")
        if not self.message_fi.strip():
            raise ValueError(f"{self.rule_id}: outcome without a Finnish message")
        if not self.evidence:
            raise ValueError(f"{self.rule_id}: outcome without evidence")
        object.__setattr__(self, "evidence", _freeze(self.evidence))

    def is_blocking(self) -> bool:
        return self.outcome != "kelpoinen"


@dataclass(frozen=True, slots=True)
class Ranked:
    """One applicant's position in the queue for one apartment.

    Ranking rules answer a different question from eligibility rules — an
    ordinal, not a pass or a fail — but they carry the same obligation to
    explain themselves, so the invariant is repeated rather than relaxed.
    """

    rank: int
    application_id: int
    rule_id: str
    message_fi: str
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("rank starts at 1")
        if not self.rule_id.strip():
            raise ValueError("ranking without a rule id")
        if not self.message_fi.strip():
            raise ValueError(f"{self.rule_id}: ranking without a Finnish message")
        if not self.evidence:
            raise ValueError(f"{self.rule_id}: ranking without evidence")
        object.__setattr__(self, "evidence", _freeze(self.evidence))


@dataclass(frozen=True, slots=True)
class MemberSnapshot:
    """One person in the household. ``None`` means not yet told to us."""

    role: Literal["paahakija", "toinen", "muu"]
    birth_year: int | None = None
    gross_monthly_income_eur: Decimal | None = None
    assets_eur: Decimal | None = None


@dataclass(frozen=True)
class ApplicationSnapshot:
    """Everything a rule may know about an application.

    ``evaluated_at`` is the injected evaluation moment. Rules read it; they never
    read a clock. Passing it here keeps the rule signature in SPEC section 5
    intact while honouring the purity constraint in section 2.3.
    """

    id: int
    evaluated_at: dt.datetime
    created_at: dt.datetime
    expires_at: dt.datetime
    members: tuple[MemberSnapshot, ...] = ()
    housing_need: Literal["asunnoton", "irtisanottu", "ahtaasti", "ei_tarvetta"] | None = None
    urgency_note: str | None = None
    order_number: str | None = None
    deposit_acknowledged: bool | None = None
    credit_default_flag: bool | None = None

    # -- derived views -----------------------------------------------------
    # Methods rather than properties so that the field-access recorder used by
    # LYHYT-EI-VARALLISUUS-01 sees the same names a rule would write by hand.

    def household_size(self) -> int:
        return len(self.members)

    def total_monthly_income(self) -> Decimal | None:
        """Sum of gross monthly income, or ``None`` if anyone has not answered.

        Source of income is deliberately not distinguished: benefits count the
        same as salary (VAPAA-MAKSU-01).
        """
        if not self.members:
            return None
        total = Decimal("0")
        for member in self.members:
            if member.gross_monthly_income_eur is None:
                return None
            total += member.gross_monthly_income_eur
        return total

    def total_assets(self) -> Decimal | None:
        if not self.members:
            return None
        total = Decimal("0")
        for member in self.members:
            if member.assets_eur is None:
                return None
            total += member.assets_eur
        return total

    def ages(self) -> tuple[int, ...] | None:
        """Ages in whole years at ``evaluated_at``.

        Only the birth year is collected, so this is the age reached during the
        evaluation year. The ASO wealth exemption is a year-granularity rule, so
        that is the honest resolution to work at.
        """
        if not self.members or any(m.birth_year is None for m in self.members):
            return None
        return tuple(self.evaluated_at.year - m.birth_year for m in self.members if m.birth_year)

    def is_expired(self) -> bool:
        return self.evaluated_at > self.expires_at


@dataclass(frozen=True, slots=True)
class UnitSnapshot:
    """The apartment a rule is deciding about."""

    id: int
    label: str
    city: str
    housing_form: Literal[
        "vapaarahoitteinen", "lyhyt_korkotuki", "tarveharkintainen", "asumisoikeus"
    ]
    listing_type: Literal["vuokra", "myynti"]
    rooms: int
    area_m2: Decimal
    rent_eur: Decimal | None = None
    price_eur: Decimal | None = None
    deposit_eur: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Limits:
    """Every threshold the rules use, injected rather than imported.

    The values live in ``seeds/limits.py`` and nowhere else. This type only says
    what shape they have.
    """

    #: housing form -> municipality group -> household size -> gross monthly EUR
    income_limits: Mapping[str, Mapping[str, Mapping[int, Decimal]]]
    #: housing form -> EUR added to the limit per person beyond the largest
    #: tabulated household size
    income_limit_per_extra_person: Mapping[str, Decimal]
    #: housing form -> household asset ceiling in EUR
    asset_limits: Mapping[str, Decimal]
    #: share of gross monthly income that rent may take
    max_rent_share_of_gross_income: Decimal
    #: age from which an applicant is exempt from the ASO wealth limit
    wealth_exemption_age: int
    adult_age: int
    max_persons_per_room: int
    #: rooms minus household size at or above which the apartment is noted as
    #: larger than the household needs
    underuse_rooms_margin: int
    order_number_pattern: str
    application_validity_months: int
    municipality_groups: Mapping[str, str]
    default_municipality_group: str

    def municipality_group(self, city: str) -> str:
        return self.municipality_groups.get(city, self.default_municipality_group)

    def income_limit(self, housing_form: str, city: str, household_size: int) -> Decimal | None:
        """Gross monthly income ceiling, or ``None`` if the form has no limit."""
        by_group = self.income_limits.get(housing_form)
        if by_group is None:
            return None
        table = by_group[self.municipality_group(city)]
        if household_size in table:
            return table[household_size]
        largest = max(table)
        extra = household_size - largest
        return table[largest] + self.income_limit_per_extra_person[housing_form] * extra

    def asset_limit(self, housing_form: str) -> Decimal | None:
        return self.asset_limits.get(housing_form)


class RecordingMember(MemberSnapshot):
    """A household member that reports field reads into a shared set.

    Without this, a regression could reach wealth data through
    ``snapshot.members[0].assets_eur`` and the guard rule would never see it.
    """

    def __init__(self, reads: set[str], **kwargs: Any) -> None:
        object.__setattr__(self, "_reads", reads)
        super().__init__(**kwargs)

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_"):
            try:
                reads: set[str] = object.__getattribute__(self, "_reads")
            except AttributeError:  # pragma: no cover - during __init__ only
                pass
            else:
                reads.add(name)
        return object.__getattribute__(self, name)


class RecordingSnapshot(ApplicationSnapshot):
    """An application snapshot that remembers which fields were read.

    LYHYT-EI-VARALLISUUS-01 has to assert that deciding a short-term subsidy
    apartment consulted no wealth or need data. A pure function cannot observe
    another function, so the engine evaluates through this wrapper and hands the
    recorded set to the guard rule as an ordinary argument — the guard stays a
    pure function of its inputs.

    Reads are recorded by attribute name, on the application and on each
    household member, so the names in the evidence are the names a rule author
    would have typed.
    """

    def __init__(self, **kwargs: Any) -> None:
        reads: set[str] = set()
        object.__setattr__(self, "_reads", reads)
        members = kwargs.get("members", ())
        kwargs["members"] = tuple(
            RecordingMember(reads, **{f.name: getattr(m, f.name) for f in fields(m)})
            for m in members
        )
        super().__init__(**kwargs)

    @classmethod
    def wrap(cls, snapshot: ApplicationSnapshot) -> Self:
        return cls(**{f.name: getattr(snapshot, f.name) for f in fields(snapshot)})

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_"):
            try:
                reads: set[str] = object.__getattribute__(self, "_reads")
            except AttributeError:  # pragma: no cover - during __init__ only
                pass
            else:
                reads.add(name)
        return object.__getattribute__(self, name)

    def _recorded_reads(self) -> frozenset[str]:
        """Underscored so that asking for the record does not itself record."""
        return frozenset(object.__getattribute__(self, "_reads"))


@dataclass(frozen=True, slots=True)
class RuleMeta:
    """Declared metadata. Drives evaluation, the adaptive form and docs/saannot.md."""

    id: str
    kind: Literal["rule", "ranking_rule", "guard_rule"]
    housing_forms: tuple[str, ...]
    requires: tuple[RequiredField, ...]
    title_fi: str
    description_fi: str
    outcomes: tuple[OutcomeValue, ...] = ()


@dataclass(frozen=True, slots=True)
class UnitDecision:
    """What one apartment's row on the decisions screen shows.

    ``outcome`` is the most blocking of ``all_outcomes`` and ``deciding`` is the
    rule that produced it, so the row can name a rule and a value without the
    frontend having to re-derive precedence.
    """

    unit_id: int
    outcome: OutcomeValue
    deciding: Outcome
    all_outcomes: Sequence[Outcome] = field(default_factory=tuple)
