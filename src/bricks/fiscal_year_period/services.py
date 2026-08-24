"""Fiscal year services — year/period lifecycle + posting-date lookup."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.bricks.fiscal_year_period.domain import (
    FiscalYear,
    FiscalYearStatus,
    Period,
    PeriodStatus,
    monthly_periods,
)


class OverlappingYearError(Exception):
    pass


class YearNotFoundError(Exception):
    pass


class PeriodNotFoundError(Exception):
    pass


def _require(
    actor: UUID | None, reason: str | None
) -> tuple[UUID, str]:
    if not actor or not reason or not reason.strip():
        raise ValueError("actor and reason are required")
    return actor, reason


class FiscalYearService:
    def __init__(self, fy_repo: Any, period_repo: Any) -> None:
        self._fy = fy_repo
        self._periods = period_repo

    def create_year(
        self,
        company_id: UUID,
        name: str,
        start_date: date,
        end_date: date,
        period_frequency: str,
        actor: UUID | None,
        reason: str | None,
    ) -> tuple[FiscalYear, list[Period]]:
        _require(actor, reason)
        if period_frequency != "MONTHLY":
            raise ValueError("Only MONTHLY frequency implemented")
        for existing in self._fy.get_by_company(company_id):
            if start_date <= existing.end_date and end_date >= existing.start_date:
                raise OverlappingYearError(f"Overlaps {existing.name}")
        fy = FiscalYear(
            id=uuid4(),
            company_id=company_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            created_by=actor,
        )
        saved_fy = self._fy.create(fy)
        periods = self._periods.create_many(monthly_periods(saved_fy, actor))
        return saved_fy, periods

    def close_period(
        self, period_id: UUID, *, actor: UUID | None, reason: str | None
    ) -> None:
        _require(actor, reason)
        period = self._periods.get_by_id(period_id)
        if period is None:
            raise PeriodNotFoundError("Không tìm thấy kỳ")
        period.status = PeriodStatus.CLOSED
        period.locked_by = actor
        period.lock_reason = reason
        self._periods.update(period)

    def reopen_period(
        self, period_id: UUID, *, actor: UUID | None, reason: str | None
    ) -> None:
        _require(actor, reason)
        period = self._periods.get_by_id(period_id)
        if period is None:
            raise PeriodNotFoundError("Không tìm thấy kỳ")
        period.status = PeriodStatus.OPEN
        period.locked_by = actor
        period.lock_reason = reason
        self._periods.update(period)

    def find_open_period(self, company_id: UUID, on_date: date) -> Period | None:
        """Posting gate: only an OPEN period containing on_date qualifies."""
        period: Period | None = self._periods.find_by_date(company_id, on_date)
        if period is not None and period.status == PeriodStatus.OPEN:
            return period
        return None

    def close_year(
        self, fiscal_year_id: UUID, *, actor: UUID | None, reason: str | None
    ) -> None:
        _require(actor, reason)
        fy = self._fy.get_by_id(fiscal_year_id)
        if fy is None:
            raise YearNotFoundError("Không tìm thấy năm tài chính")
        for period in self._periods.get_by_year(fiscal_year_id):
            period.status = PeriodStatus.CLOSED
            period.locked_by = actor
            period.lock_reason = reason
            self._periods.update(period)
        fy.status = FiscalYearStatus.YEAR_CLOSED
        self._fy.update(fy)
