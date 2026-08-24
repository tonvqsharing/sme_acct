"""Fiscal year & period domain. Pure Python."""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from uuid import UUID, uuid4


class FiscalYearStatus(Enum):
    OPEN = "OPEN"
    YEAR_CLOSED = "YEAR_CLOSED"


class PeriodStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class FiscalYear:
    id: UUID
    company_id: UUID
    name: str
    start_date: date
    end_date: date
    status: FiscalYearStatus = FiscalYearStatus.OPEN
    created_by: UUID | None = None

    def __post_init__(self) -> None:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if (self.end_date - self.start_date).days > 366 + 31:
            raise ValueError("Fiscal year may not exceed ~15 months")


@dataclass
class Period:
    fiscal_year_id: UUID
    company_id: UUID
    sequence: int
    start_date: date
    end_date: date
    id: UUID = field(default_factory=uuid4)
    status: PeriodStatus = PeriodStatus.OPEN
    locked_by: UUID | None = None
    lock_reason: str | None = None


def monthly_periods(fy: FiscalYear, actor: UUID | None) -> list[Period]:
    """Split a fiscal year into calendar months."""
    periods: list[Period] = []
    y, m = fy.start_date.year, fy.start_date.month
    seq = 1
    while (y, m) <= (fy.end_date.year, fy.end_date.month):
        last = calendar.monthrange(y, m)[1]
        p_start = max(date(y, m, 1), fy.start_date)
        p_end = min(date(y, m, last), fy.end_date)
        periods.append(
            Period(
                fiscal_year_id=fy.id,
                company_id=fy.company_id,
                sequence=seq,
                start_date=p_start,
                end_date=p_end,
            )
        )
        seq += 1
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return periods
