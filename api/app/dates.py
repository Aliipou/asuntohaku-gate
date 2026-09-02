"""Calendar arithmetic for application validity.

An application is valid for a number of *months*, not a number of days, so the
expiry of one created on 31 January is 30 April and not 2 May. Kept out of the
rule modules: rules receive ``expires_at`` already computed.
"""

from __future__ import annotations

import calendar
import datetime as dt


def add_months(moment: dt.datetime, months: int) -> dt.datetime:
    """Add whole months, clamping to the last day of a shorter target month."""
    index = moment.month - 1 + months
    year = moment.year + index // 12
    month = index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def expiry_for(created_at: dt.datetime, validity_months: int) -> dt.datetime:
    return add_months(created_at, validity_months)
