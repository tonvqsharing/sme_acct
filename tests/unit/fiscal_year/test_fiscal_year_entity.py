"""Unit tests — FiscalYear / AccountingPeriod entities (specs §2.2, rules R-01..R-03, R-08, R-10).

Covers test-plan U-01..U-06, U-08..U-16 (entity-level; service cases in
test_period_lock_service.py).
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.domain.entities.base import AccountingPeriodType, PeriodStatus
from src.domain.entities.fiscal_year import AccountingPeriod, FiscalYear
from src.domain.exceptions import (
    InvalidFiscalYearError,
    PeriodTransitionError,
)

COMPANY = uuid4()


def _cal_fy(start: date, **kw) -> FiscalYear:
    return FiscalYear(company_id=COMPANY, period_type=AccountingPeriodType.CALENDAR, start_date=start, **kw)


class TestFiscalYearConstruction:
    def test_u01_calendar_2026_12_periods(self):
        fy = _cal_fy(date(2026, 1, 1))
        assert fy.end_date == date(2026, 12, 31)
        assert len(fy.periods) == 12
        assert fy.periods[0].start_date == date(2026, 1, 1)
        assert fy.periods[11].end_date == date(2026, 12, 31)

    def test_u02_fiscal_apr_2026(self):
        fy = FiscalYear(
            company_id=COMPANY,
            period_type=AccountingPeriodType.FISCAL_APR,
            start_date=date(2026, 4, 1),
        )
        assert fy.end_date == date(2027, 3, 31)
        assert len(fy.periods) == 12
        assert fy.periods[0].label == "Tháng 04/2026"

    def test_u03_fiscal_jul_and_oct(self):
        for ptype, start, end in [
            (AccountingPeriodType.FISCAL_JUL, date(2026, 7, 1), date(2027, 6, 30)),
            (AccountingPeriodType.FISCAL_OCT, date(2026, 10, 1), date(2027, 9, 30)),
        ]:
            fy = FiscalYear(company_id=COMPANY, period_type=ptype, start_date=start)
            assert fy.end_date == end
            assert len(fy.periods) == 12

    def test_u04_non_quarter_start_rejected(self):
        with pytest.raises(InvalidFiscalYearError, match="quý"):
            _cal_fy(date(2026, 7, 15))  # mid-quarter start — illegal (R-01)

    def test_u04b_calendar_start_not_jan1_rejected(self):
        with pytest.raises(InvalidFiscalYearError):
            _cal_fy(date(2026, 2, 1))

    def test_u05_first_period_15_months_max(self):
        fy = _cal_fy(date(2026, 8, 15), is_first_period=True, end_date=date(2026, 12, 31))
        assert fy.is_first_period
        assert fy.label == "Kỳ kế toán đầu tiên"
        assert fy.periods[0].start_date == date(2026, 8, 15)
        assert fy.periods[-1].end_date == date(2026, 12, 31)

    def test_u06_first_period_over_15_months_rejected(self):
        with pytest.raises(InvalidFiscalYearError, match="15 tháng"):
            _cal_fy(date(2024, 11, 1), is_first_period=True, end_date=date(2026, 12, 31))

    def test_u09_leap_year_period_end(self):
        fy = _cal_fy(date(2024, 1, 1))
        assert fy.periods[1].start_date == date(2024, 2, 1)
        assert fy.periods[1].end_date == date(2024, 2, 29)

    def test_u08_periods_contiguous_non_overlapping(self):
        fy = _cal_fy(date(2026, 1, 1))
        for prev, cur in zip(fy.periods, fy.periods[1:]):
            assert prev.end_date + (date(2026, 1, 2) - date(2026, 1, 1)) == cur.start_date
        assert fy.periods[0].start_date == fy.start_date
        assert fy.periods[-1].end_date == fy.end_date


class TestPeriodLookup:
    def _fy(self) -> FiscalYear:
        return _cal_fy(date(2026, 1, 1))

    def test_u16_boundary_dates_inclusive(self):
        fy = self._fy()
        assert fy.period_for_date(date(2026, 1, 1)).period_number == 1
        assert fy.period_for_date(date(2026, 12, 31)).period_number == 12

    def test_contains_out_of_range(self):
        fy = self._fy()
        assert fy.period_for_date(date(2025, 12, 31)) is None
        assert fy.period_for_date(date(2027, 1, 1)) is None

    def test_u15_locked_lookup(self):
        fy = self._fy()
        p = fy.period_for_date(date(2026, 2, 15))
        p.close(actor=uuid4(), reason="hết tháng")
        assert fy.is_locked(date(2026, 2, 15)) is True
        assert fy.is_locked(date(2026, 3, 1)) is False


class TestPeriodStateMachine:
    def _period(self) -> AccountingPeriod:
        return AccountingPeriod(
            fiscal_year_id=uuid4(),
            period_number=1,
            label="Tháng 01/2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    def test_u10_open_to_locked(self):
        p = self._period()
        actor = uuid4()
        p.close(actor=actor, reason="khóa sổ")
        assert p.status == PeriodStatus.LOCKED
        assert p.locked_by == actor
        assert p.lock_reason == "khóa sổ"

    def test_u11_open_to_year_closed_rejected(self):
        p = self._period()
        with pytest.raises(PeriodTransitionError):
            p.close_fiscal_year()

    def test_locked_to_year_closed_ok(self):
        p = self._period()
        p.close(actor=uuid4(), reason="x")
        p.close_fiscal_year()
        assert p.status == PeriodStatus.YEAR_CLOSED

    def test_u12_year_closed_cannot_reopen(self):
        p = self._period()
        p.close(actor=uuid4(), reason="x")
        p.close_fiscal_year()
        with pytest.raises(PeriodTransitionError):
            p.reopen(actor=uuid4(), reason="mở lại")

    def test_reopen_locked_ok(self):
        p = self._period()
        p.close(actor=uuid4(), reason="x")
        p.reopen(actor=uuid4(), reason="điều chỉnh")
        assert p.status == PeriodStatus.OPEN

    def test_double_close_rejected(self):
        p = self._period()
        p.close(actor=uuid4(), reason="x")
        with pytest.raises(PeriodTransitionError):
            p.close(actor=uuid4(), reason="lần 2")