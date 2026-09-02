"""Thresholds used by the rule engine.

EVERY FIGURE IN THIS FILE IS INVENTED FOR THIS DEMO.

None of these numbers is a current statutory limit, and none of them is taken
from ARA, a municipality or any housing operator. They are plausible-looking
placeholders whose only job is to make the rule engine and the decisions screen
demonstrable. Do not read them as guidance about any real application.

This is the only file in the repository that holds a threshold. If a number with
policy meaning appears anywhere else, that is a bug.
"""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

from api.rules.types import Limits

# Municipality groups. The capital region is treated as one market, everything
# else as another. Invented split, invented figures.
MUNICIPALITY_GROUPS = MappingProxyType(
    {
        "Helsinki": "paakaupunkiseutu",
        "Espoo": "paakaupunkiseutu",
        "Vantaa": "paakaupunkiseutu",
        "Kauniainen": "paakaupunkiseutu",
        "Tampere": "muu_suomi",
    }
)
DEFAULT_MUNICIPALITY_GROUP = "muu_suomi"

# Gross monthly household income ceilings, by housing form, municipality group
# and household size. Free-financed stock has no income ceiling at all — it is
# gated on rent-paying ability instead — so it is absent from this table rather
# than given an unreachable number.
INCOME_LIMITS = MappingProxyType(
    {
        "lyhyt_korkotuki": MappingProxyType(
            {
                "paakaupunkiseutu": MappingProxyType(
                    {
                        1: Decimal("3800"),
                        2: Decimal("5600"),
                        3: Decimal("7100"),
                        4: Decimal("8400"),
                    }
                ),
                "muu_suomi": MappingProxyType(
                    {
                        1: Decimal("3400"),
                        2: Decimal("5000"),
                        3: Decimal("6400"),
                        4: Decimal("7600"),
                    }
                ),
            }
        ),
        "tarveharkintainen": MappingProxyType(
            {
                "paakaupunkiseutu": MappingProxyType(
                    {
                        1: Decimal("3100"),
                        2: Decimal("4600"),
                        3: Decimal("5900"),
                        4: Decimal("7000"),
                    }
                ),
                "muu_suomi": MappingProxyType(
                    {
                        1: Decimal("2800"),
                        2: Decimal("4200"),
                        3: Decimal("5300"),
                        4: Decimal("6300"),
                    }
                ),
            }
        ),
    }
)

# Added to the ceiling for each person beyond the largest tabulated household.
INCOME_LIMIT_PER_EXTRA_PERSON = MappingProxyType(
    {
        "lyhyt_korkotuki": Decimal("1100"),
        "tarveharkintainen": Decimal("900"),
    }
)

# Household asset ceilings. Right-of-occupancy has no income limit but does have
# a wealth limit; free-financed and short-term subsidy stock have neither.
ASSET_LIMITS = MappingProxyType(
    {
        "tarveharkintainen": Decimal("42000"),
        "asumisoikeus": Decimal("95000"),
    }
)

# Rent may take at most this share of gross monthly household income
# (VAPAA-MAKSU-01).
MAX_RENT_SHARE_OF_GROSS_INCOME = Decimal("0.35")

# Age from which an applicant is exempt from the right-of-occupancy wealth limit.
WEALTH_EXEMPTION_AGE = 55

ADULT_AGE = 18

# Household size against apartment size (YLEIS-KOKO-01).
MAX_PERSONS_PER_ROOM = 2
UNDERUSE_ROOMS_MARGIN = 2

# Right-of-occupancy order number format. Invented for the demo: six digits.
ORDER_NUMBER_PATTERN = r"^\d{6}$"

# An application is valid for this many months from creation
# (YLEIS-VANHENTUNUT-01).
APPLICATION_VALIDITY_MONTHS = 3

DEMO_LIMITS = Limits(
    income_limits=INCOME_LIMITS,
    income_limit_per_extra_person=INCOME_LIMIT_PER_EXTRA_PERSON,
    asset_limits=ASSET_LIMITS,
    max_rent_share_of_gross_income=MAX_RENT_SHARE_OF_GROSS_INCOME,
    wealth_exemption_age=WEALTH_EXEMPTION_AGE,
    adult_age=ADULT_AGE,
    max_persons_per_room=MAX_PERSONS_PER_ROOM,
    underuse_rooms_margin=UNDERUSE_ROOMS_MARGIN,
    order_number_pattern=ORDER_NUMBER_PATTERN,
    application_validity_months=APPLICATION_VALIDITY_MONTHS,
    municipality_groups=MUNICIPALITY_GROUPS,
    default_municipality_group=DEFAULT_MUNICIPALITY_GROUP,
)
