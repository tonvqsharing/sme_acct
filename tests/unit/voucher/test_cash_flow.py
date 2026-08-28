"""Tests for cash flow classification — B03-DN support."""

from __future__ import annotations

from src.bricks.voucher.domain import CashFlowClass


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
