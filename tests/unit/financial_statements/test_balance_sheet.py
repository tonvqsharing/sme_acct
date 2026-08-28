"""Tests for Balance Sheet (B01-DN) computation and validation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.bricks.financial_statements.services import (
    BalanceSheetImbalanceError,
    BalanceSheetService,
    ReportEngine,
)
from src.bricks.financial_statements.templates import b01_dn_template

ZERO = Decimal(0)


class TestBalanceSheetComputation:
    """B01-DN computation — balanced sheet tests via BalanceSheetService."""

    def test_balanced_sheet(self) -> None:
        """Assets = Liabilities + Equity → no error."""
        tmpl = b01_dn_template()
        svc = BalanceSheetService()
        balances = {
            "111": {"debit": Decimal(500), "credit": ZERO},
            "214": {"debit": Decimal(1000), "credit": ZERO},
            "331": {"debit": ZERO, "credit": Decimal(300)},
            "411": {"debit": ZERO, "credit": Decimal(1200)},
        }
        lines = svc.compute(tmpl, balances)

        ts = next(l for l in lines if l.line_code == "TS_TONG")
        nnc = next(l for l in lines if l.line_code == "NNC_TONG")
        check = next(l for l in lines if l.line_code == "CHECK")

        assert ts.value_current == Decimal(1500)
        assert nnc.value_current == Decimal(1500)
        assert check.value_current == ZERO

    def test_imbalanced_sheet_raises(self) -> None:
        """Assets != Liabilities + Equity → BalanceSheetImbalanceError."""
        tmpl = b01_dn_template()
        svc = BalanceSheetService()
        balances = {
            "111": {"debit": Decimal(500), "credit": ZERO},
            "331": {"debit": ZERO, "credit": Decimal(300)},
            "411": {"debit": ZERO, "credit": Decimal(100)},
        }
        with pytest.raises(BalanceSheetImbalanceError, match="imbalance"):
            svc.compute(tmpl, balances)

    def test_empty_balances(self) -> None:
        """All zeros → balanced."""
        tmpl = b01_dn_template()
        svc = BalanceSheetService()
        lines = svc.compute(tmpl, {})
        check = next(l for l in lines if l.line_code == "CHECK")
        assert check.value_current == ZERO


class TestBalanceSheetPartials:
    """Individual section tests using ReportEngine (no balance validation)."""

    def test_short_term_assets_group(self) -> None:
        """A_TONG sums short-term asset children."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            "111": {"debit": Decimal(100), "credit": ZERO},
            "112": {"debit": Decimal(200), "credit": ZERO},
            "131": {"debit": Decimal(50), "credit": ZERO},
        }
        lines = engine.compute(tmpl, balances)
        a_tong = next(l for l in lines if l.line_code == "A_TONG")
        assert a_tong.value_current == Decimal(350)

    def test_long_term_assets_group(self) -> None:
        """B_TONG sums long-term asset children (contra netted)."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            "214": {"debit": Decimal(1000), "credit": ZERO},
            "213": {"debit": ZERO, "credit": Decimal(50)},
        }
        lines = engine.compute(tmpl, balances)
        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        assert b_tong.value_current == Decimal(950)

    def test_liabilities_group(self) -> None:
        """C_TONG sums liability children."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            "331": {"debit": ZERO, "credit": Decimal(300)},
            "341": {"debit": ZERO, "credit": Decimal(200)},
        }
        lines = engine.compute(tmpl, balances)
        c_tong = next(l for l in lines if l.line_code == "C_TONG")
        assert c_tong.value_current == Decimal(500)

    def test_equity_group(self) -> None:
        """D_TONG sums equity children."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            "411": {"debit": ZERO, "credit": Decimal(1000)},
            "421": {"debit": ZERO, "credit": Decimal(500)},
        }
        lines = engine.compute(tmpl, balances)
        d_tong = next(l for l in lines if l.line_code == "D_TONG")
        assert d_tong.value_current == Decimal(1500)

    def test_contra_accounts_net_correctly(self) -> None:
        """Accumulated depreciation reduces fixed assets without sign flip."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            "214": {"debit": Decimal(5000), "credit": ZERO},
            "213": {"debit": ZERO, "credit": Decimal(2000)},
        }
        lines = engine.compute(tmpl, balances)
        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        assert b_tong.value_current == Decimal(3000)


class TestBalanceSheetRealistic:
    """Full realistic balance sheet scenario."""

    def test_realistic_balanced(self) -> None:
        """Company with assets, liabilities, equity — must balance."""
        tmpl = b01_dn_template()
        svc = BalanceSheetService()
        # Total assets = 260M + 300M = 560M
        # Total liab+equity = 260M + 300M = 560M
        balances = {
            # Short-term assets: 260M
            "111": {"debit": Decimal(50_000_000), "credit": ZERO},
            "112": {"debit": Decimal(100_000_000), "credit": ZERO},
            "131": {"debit": Decimal(30_000_000), "credit": ZERO},
            "151": {"debit": Decimal(80_000_000), "credit": ZERO},
            # Long-term assets: 300M (500 cost - 200 depr)
            "214": {"debit": Decimal(500_000_000), "credit": ZERO},
            "213": {"debit": ZERO, "credit": Decimal(200_000_000)},
            # Liabilities: 260M
            "331": {"debit": ZERO, "credit": Decimal(60_000_000)},
            "341": {"debit": ZERO, "credit": Decimal(200_000_000)},
            # Equity: 300M (= 560M - 260M)
            "411": {"debit": ZERO, "credit": Decimal(200_000_000)},
            "421": {"debit": ZERO, "credit": Decimal(100_000_000)},
        }
        lines = svc.compute(tmpl, balances)
        check = next(l for l in lines if l.line_code == "CHECK")
        assert check.value_current == ZERO

    def test_section_totals(self) -> None:
        """Verify each section total independently."""
        tmpl = b01_dn_template()
        engine = ReportEngine()
        balances = {
            # Short-term assets
            "111": {"debit": Decimal(50_000_000), "credit": ZERO},
            "112": {"debit": Decimal(100_000_000), "credit": ZERO},
            "131": {"debit": Decimal(30_000_000), "credit": ZERO},
            "151": {"debit": Decimal(80_000_000), "credit": ZERO},
            # Long-term assets
            "214": {"debit": Decimal(500_000_000), "credit": ZERO},
            "213": {"debit": ZERO, "credit": Decimal(200_000_000)},
            # Liabilities
            "331": {"debit": ZERO, "credit": Decimal(60_000_000)},
            "341": {"debit": ZERO, "credit": Decimal(200_000_000)},
            # Equity
            "411": {"debit": ZERO, "credit": Decimal(200_000_000)},
            "421": {"debit": ZERO, "credit": Decimal(100_000_000)},
        }
        lines = engine.compute(tmpl, balances)

        a_tong = next(l for l in lines if l.line_code == "A_TONG")
        assert a_tong.value_current == Decimal(260_000_000)

        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        assert b_tong.value_current == Decimal(300_000_000)

        ts = next(l for l in lines if l.line_code == "TS_TONG")
        assert ts.value_current == Decimal(560_000_000)

        c_tong = next(l for l in lines if l.line_code == "C_TONG")
        assert c_tong.value_current == Decimal(260_000_000)

        d_tong = next(l for l in lines if l.line_code == "D_TONG")
        assert d_tong.value_current == Decimal(300_000_000)

        nnc = next(l for l in lines if l.line_code == "NNC_TONG")
        assert nnc.value_current == Decimal(560_000_000)
