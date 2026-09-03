"""Tests for Cash Flow Statement (B03-DN) template and computation."""

from __future__ import annotations

from decimal import Decimal

from src.bricks.financial_statements.services import CashFlowService
from src.bricks.financial_statements.templates import b03_dn_template

ZERO = Decimal(0)


class TestB03DNTemplate:
    """B03-DN template structure."""

    def test_template_code(self) -> None:
        tmpl = b03_dn_template()
        assert tmpl.code == "B03-DN"
        assert tmpl.name == "Báo cáo lưu chuyển tiền tệ"

    def test_has_all_sections(self) -> None:
        tmpl = b03_dn_template()
        codes = {l.line_code for l in tmpl.lines}
        # Operating
        assert "A" in codes
        assert "A1" in codes
        assert "A2" in codes
        assert "A3" in codes
        assert "A4" in codes
        assert "A_TONG" in codes
        # Investing
        assert "B" in codes
        assert "B1" in codes
        assert "B2" in codes
        assert "B_TONG" in codes
        # Financing
        assert "C" in codes
        assert "C1" in codes
        assert "C2" in codes
        assert "C3" in codes
        assert "C4" in codes
        assert "C_TONG" in codes
        # Totals
        assert "NET_CF" in codes
        assert "CASH_BEGIN" in codes
        assert "CASH_END" in codes

    def test_cash_flow_items_have_class(self) -> None:
        """All CASH_FLOW_ITEM lines have cash_flow_class set."""
        tmpl = b03_dn_template()
        cf_codes = ["A1", "A2", "A3", "A4", "B1", "B2", "C1", "C2", "C3", "C4"]
        cf_items = [l for l in tmpl.lines if l.line_code in cf_codes]
        for item in cf_items:
            assert item.cash_flow_class is not None

    def test_net_cf_formula(self) -> None:
        tmpl = b03_dn_template()
        ncf = next(l for l in tmpl.lines if l.line_code == "NET_CF")
        assert ncf.formula == "A_TONG+B_TONG+C_TONG"

    def test_cash_end_formula(self) -> None:
        tmpl = b03_dn_template()
        ce = next(l for l in tmpl.lines if l.line_code == "CASH_END")
        assert ce.formula == "NET_CF+CASH_BEGIN"


class TestCashFlowComputation:
    """B03-DN computation from cash flow data."""

    def test_operating_activities(self) -> None:
        """Operating cash flows computed correctly."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        # Each line gets its own amount
        cf_amounts = {
            "A1": Decimal(500),  # Cash received from customers
            "A2": Decimal(-300),  # Cash paid to suppliers
            "A3": Decimal(-100),  # Cash paid to employees
            "A4": Decimal(-50),  # Cash paid for tax
        }
        lines = svc.compute(tmpl, cf_amounts, opening_cash=ZERO)

        a1 = next(l for l in lines if l.line_code == "A1")
        assert a1.value_current == Decimal(500)

        a2 = next(l for l in lines if l.line_code == "A2")
        assert a2.value_current == Decimal(-300)

        a_tong = next(l for l in lines if l.line_code == "A_TONG")
        # 500 + (-300) + (-100) + (-50) = 50
        assert a_tong.value_current == Decimal(50)

    def test_investing_activities(self) -> None:
        """Investing cash flows computed correctly."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        cf_amounts = {
            "B1": Decimal(-200),  # Purchase of fixed assets
            "B2": Decimal(80),  # Proceeds from sale
        }
        lines = svc.compute(tmpl, cf_amounts, opening_cash=ZERO)

        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        # (-200) + 80 = -120
        assert b_tong.value_current == Decimal(-120)

    def test_financing_activities(self) -> None:
        """Financing cash flows computed correctly."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        cf_amounts = {
            "C1": Decimal(300),  # Proceeds from borrowings
            "C2": Decimal(-100),  # Repayment of borrowings
            "C3": Decimal(200),  # Capital contributions
            "C4": Decimal(-50),  # Dividends paid
        }
        lines = svc.compute(tmpl, cf_amounts, opening_cash=ZERO)

        c_tong = next(l for l in lines if l.line_code == "C_TONG")
        # 300 + (-100) + 200 + (-50) = 350
        assert c_tong.value_current == Decimal(350)

    def test_net_increase_decrease(self) -> None:
        """NET_CF = sum of section totals."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        cf_amounts = {
            "A1": Decimal(500),  # Operating: 500
            "B1": Decimal(-200),  # Investing: -200
            "C1": Decimal(100),  # Financing: 100
        }
        lines = svc.compute(tmpl, cf_amounts, opening_cash=ZERO)

        a_tong = next(l for l in lines if l.line_code == "A_TONG")
        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        c_tong = next(l for l in lines if l.line_code == "C_TONG")

        net = next(l for l in lines if l.line_code == "NET_CF")
        assert (
            net.value_current == a_tong.value_current + b_tong.value_current + c_tong.value_current
        )

    def test_cash_reconciliation(self) -> None:
        """CASH_END = NET_CF + CASH_BEGIN."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        cf_amounts = {"A1": Decimal(500)}
        lines = svc.compute(tmpl, cf_amounts, opening_cash=Decimal(1000))

        net = next(l for l in lines if l.line_code == "NET_CF")
        begin = next(l for l in lines if l.line_code == "CASH_BEGIN")
        end = next(l for l in lines if l.line_code == "CASH_END")

        assert begin.value_current == Decimal(1000)
        assert end.value_current == net.value_current + Decimal(1000)

    def test_empty_cash_flows(self) -> None:
        """All zeros → balanced."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        lines = svc.compute(tmpl, {}, opening_cash=ZERO)
        end = next(l for l in lines if l.line_code == "CASH_END")
        assert end.value_current == ZERO

    def test_realistic_scenario(self) -> None:
        """Company with all three activity types."""
        tmpl = b03_dn_template()
        svc = CashFlowService()
        cf_amounts = {
            # Operating
            "A1": Decimal(800_000_000),  # Received from customers
            "A2": Decimal(-400_000_000),  # Paid to suppliers
            "A3": Decimal(-150_000_000),  # Paid to employees
            "A4": Decimal(-50_000_000),  # Tax
            # Investing
            "B1": Decimal(-300_000_000),  # Buy fixed assets
            "B2": Decimal(50_000_000),  # Sell fixed assets
            # Financing
            "C1": Decimal(200_000_000),  # Borrow
            "C2": Decimal(-100_000_000),  # Repay
            "C3": Decimal(100_000_000),  # Capital
            "C4": Decimal(-50_000_000),  # Dividends
        }
        lines = svc.compute(tmpl, cf_amounts, opening_cash=Decimal(100_000_000))

        a_tong = next(l for l in lines if l.line_code == "A_TONG")
        # 800M - 400M - 150M - 50M = 200M
        assert a_tong.value_current == Decimal(200_000_000)

        b_tong = next(l for l in lines if l.line_code == "B_TONG")
        # -300M + 50M = -250M
        assert b_tong.value_current == Decimal(-250_000_000)

        c_tong = next(l for l in lines if l.line_code == "C_TONG")
        # 200M - 100M + 100M - 50M = 150M
        assert c_tong.value_current == Decimal(150_000_000)

        net = next(l for l in lines if l.line_code == "NET_CF")
        # 200M + (-250M) + 150M = 100M
        assert net.value_current == Decimal(100_000_000)

        end = next(l for l in lines if l.line_code == "CASH_END")
        # 100M + 100M = 200M
        assert end.value_current == Decimal(200_000_000)
