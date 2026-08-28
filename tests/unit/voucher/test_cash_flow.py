"""Tests for cash flow classification — B03-DN support."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.bricks.voucher.domain import CashFlowClass, JournalLine


class TestCashFlowClass:
    """CashFlowClass enum values."""

    def test_operating_value(self) -> None:
        assert CashFlowClass.OPERATING.value == "operating"

    def test_investing_value(self) -> None:
        assert CashFlowClass.INVESTING.value == "investing"

    def test_financing_value(self) -> None:
        assert CashFlowClass.FINANCING.value == "financing"

    def test_all_types_covered(self) -> None:
        types = {t.value for t in CashFlowClass}
        assert types == {"operating", "investing", "financing"}


class TestJournalLineCashFlow:
    """JournalLine with cash_flow_class field."""

    def test_cash_flow_class_optional(self) -> None:
        line = JournalLine(account_code="111", debit=Decimal(100))
        assert line.cash_flow_class is None

    def test_cash_flow_class_set(self) -> None:
        line = JournalLine(
            account_code="111",
            debit=Decimal(100),
            bank_account_id=uuid4(),
            cash_flow_class=CashFlowClass.OPERATING,
        )
        assert line.cash_flow_class == CashFlowClass.OPERATING

    def test_non_cash_line_no_validation(self) -> None:
        """Non-cash lines don't need cash_flow_class."""
        line = JournalLine(account_code="5111", credit=Decimal(100))
        assert line.cash_flow_class is None
