"""Unit tests — fiscal year domain enums + exceptions (rules-fiscal-year.md A1, R-01, R-15)."""

from __future__ import annotations

import pytest

from src.domain.entities.base import (
    AccountingPeriodType,
    PeriodLockAction,
    PeriodStatus,
)
from src.domain.exceptions import (
    DomainException,
    FiscalYearError,
    FiscalYearExistsError,
    InvalidFiscalYearError,
    PeriodNotClosableError,
    PeriodTransitionError,
    SelfApprovalError,
    YearEndPreconditionsError,
)


class TestAccountingPeriodType:
    def test_legal_values_only(self):
        """Luật Kế toán 88/2015 Đ12: fiscal year starts quarter-aligned."""
        assert {t.value for t in AccountingPeriodType} == {
            "calendar",
            "fiscal_apr",
            "fiscal_jul",
            "fiscal_oct",
        }

    def test_fiscal_15_removed(self):
        """R-15: 15-month mid-quarter start is ILLEGAL — must not exist."""
        with pytest.raises(AttributeError):
            AccountingPeriodType.FISCAL_15  # noqa: B018

    def test_calendar_members(self):
        assert AccountingPeriodType.CALENDAR.value == "calendar"
        assert AccountingPeriodType.FISCAL_APR.value == "fiscal_apr"
        assert AccountingPeriodType.FISCAL_JUL.value == "fiscal_jul"
        assert AccountingPeriodType.FISCAL_OCT.value == "fiscal_oct"


class TestPeriodStatus:
    def test_values(self):
        assert PeriodStatus.OPEN.value == "OPEN"
        assert PeriodStatus.LOCKED.value == "LOCKED"
        assert PeriodStatus.YEAR_CLOSED.value == "YEAR_CLOSED"

    def test_all_states_present(self):
        assert {s.value for s in PeriodStatus} == {"OPEN", "LOCKED", "YEAR_CLOSED"}


class TestPeriodLockAction:
    def test_values(self):
        assert PeriodLockAction.CLOSE.value == "CLOSE"
        assert PeriodLockAction.REOPEN.value == "REOPEN"
        assert PeriodLockAction.YEAR_END.value == "YEAR_END"


class TestFiscalYearExceptions:
    def test_hierarchy(self):
        assert issubclass(FiscalYearError, DomainException)
        assert issubclass(InvalidFiscalYearError, FiscalYearError)
        assert issubclass(FiscalYearExistsError, FiscalYearError)
        assert issubclass(PeriodTransitionError, FiscalYearError)
        assert issubclass(PeriodNotClosableError, FiscalYearError)
        assert issubclass(YearEndPreconditionsError, FiscalYearError)
        assert issubclass(SelfApprovalError, FiscalYearError)

    def test_raise_and_message(self):
        with pytest.raises(InvalidFiscalYearError, match="quý"):
            raise InvalidFiscalYearError(
                "Năm tài chính phải bắt đầu từ đầu tháng đầu quý (01/01, 01/04, 01/07, 01/10)"
            )
