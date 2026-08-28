"""Tests for Income Statement (B02-DN) template and computation."""

from __future__ import annotations

from decimal import Decimal

from src.bricks.financial_statements.services import IncomeStatementService, ReportEngine
from src.bricks.financial_statements.templates import b02_dn_template

ZERO = Decimal(0)


class TestB02DNTemplate:
    """B02-DN template structure."""

    def test_template_code(self) -> None:
        tmpl = b02_dn_template()
        assert tmpl.code == "B02-DN"
        assert tmpl.name == "Báo cáo kết quả hoạt động kinh doanh"

    def test_has_all_sections(self) -> None:
        tmpl = b02_dn_template()
        codes = {l.line_code for l in tmpl.lines}
        # Revenue
        assert "A" in codes  # Gross revenue
        assert "A_DISC" in codes  # Discounts
        assert "A_NET" in codes  # Net revenue formula
        # COGS
        assert "B" in codes
        # Gross profit
        assert "GROSS_PROFIT" in codes
        # Operating expenses
        assert "C" in codes  # Sales expenses
        assert "D" in codes  # Admin expenses
        # Operating profit
        assert "OP_PROFIT" in codes
        # Financial
        assert "E" in codes  # Financial income
        assert "F" in codes  # Financial expenses
        assert "NET_FIN" in codes
        # Other
        assert "G" in codes  # Other income
        assert "H" in codes  # Other expenses
        # Profit
        assert "PROFIT_BT" in codes  # Before tax
        assert "I" in codes  # Tax
        assert "NET_PROFIT" in codes

    def test_gross_profit_formula(self) -> None:
        tmpl = b02_dn_template()
        gp = next(l for l in tmpl.lines if l.line_code == "GROSS_PROFIT")
        assert gp.formula == "A_NET-B"

    def test_operating_profit_formula(self) -> None:
        tmpl = b02_dn_template()
        op = next(l for l in tmpl.lines if l.line_code == "OP_PROFIT")
        assert op.formula == "GROSS_PROFIT-C-D"

    def test_net_profit_formula(self) -> None:
        tmpl = b02_dn_template()
        np = next(l for l in tmpl.lines if l.line_code == "NET_PROFIT")
        assert np.formula == "PROFIT_BT-I"

    def test_revenue_sign_flip(self) -> None:
        """Revenue accounts have sign=-1 for credit balance."""
        tmpl = b02_dn_template()
        a = next(l for l in tmpl.lines if l.line_code == "A")
        assert a.sign == -1

    def test_expense_sign_default(self) -> None:
        """Expense accounts have sign=1 (debit balance)."""
        tmpl = b02_dn_template()
        b = next(l for l in tmpl.lines if l.line_code == "B")
        assert b.sign == 1


class TestIncomeStatementComputation:
    """B02-DN computation from account balances."""

    def test_profitable_company(self) -> None:
        """Revenue > all expenses → positive net profit."""
        tmpl = b02_dn_template()
        svc = IncomeStatementService()
        balances = {
            # Revenue: 1000
            "511": {"debit": ZERO, "credit": Decimal(1000)},
            # COGS: 400
            "632": {"debit": Decimal(400), "credit": ZERO},
            # Sales exp: 100
            "641": {"debit": Decimal(100), "credit": ZERO},
            # Admin exp: 150
            "642": {"debit": Decimal(150), "credit": ZERO},
            # Financial income: 50
            "515": {"debit": ZERO, "credit": Decimal(50)},
            # Financial exp: 20
            "635": {"debit": Decimal(20), "credit": ZERO},
            # Other income: 30
            "711": {"debit": ZERO, "credit": Decimal(30)},
            # Other exp: 10
            "811": {"debit": Decimal(10), "credit": ZERO},
            # Tax: 100
            "821": {"debit": Decimal(100), "credit": ZERO},
        }
        lines = svc.compute(tmpl, balances)

        # Net revenue = 1000 (sign flip: -1 * (0-1000) = 1000)
        a_net = next(l for l in lines if l.line_code == "A_NET")
        assert a_net.value_current == Decimal(1000)

        # COGS = 400
        b = next(l for l in lines if l.line_code == "B")
        assert b.value_current == Decimal(400)

        # Gross profit = 1000 - 400 = 600
        gp = next(l for l in lines if l.line_code == "GROSS_PROFIT")
        assert gp.value_current == Decimal(600)

        # Operating profit = 600 - 100 - 150 = 350
        op = next(l for l in lines if l.line_code == "OP_PROFIT")
        assert op.value_current == Decimal(350)

        # Net financial = 50 - 20 = 30
        nf = next(l for l in lines if l.line_code == "NET_FIN")
        assert nf.value_current == Decimal(30)

        # Profit before tax = 350 + 30 + 30 - 10 = 400
        pbt = next(l for l in lines if l.line_code == "PROFIT_BT")
        assert pbt.value_current == Decimal(400)

        # Net profit = 400 - 100 = 300
        np = next(l for l in lines if l.line_code == "NET_PROFIT")
        assert np.value_current == Decimal(300)

    def test_loss_company(self) -> None:
        """Expenses > revenue → negative net profit."""
        tmpl = b02_dn_template()
        svc = IncomeStatementService()
        balances = {
            # Revenue: 200
            "511": {"debit": ZERO, "credit": Decimal(200)},
            # COGS: 150
            "632": {"debit": Decimal(150), "credit": ZERO},
            # Sales exp: 100
            "641": {"debit": Decimal(100), "credit": ZERO},
            # Admin exp: 50
            "642": {"debit": Decimal(50), "credit": ZERO},
        }
        lines = svc.compute(tmpl, balances)

        # Net revenue = 200
        a_net = next(l for l in lines if l.line_code == "A_NET")
        assert a_net.value_current == Decimal(200)

        # Operating profit = 200 - 150 - 100 - 50 = -100
        op = next(l for l in lines if l.line_code == "OP_PROFIT")
        assert op.value_current == Decimal(-100)

    def test_with_sales_discounts(self) -> None:
        """Sales discounts reduce net revenue."""
        tmpl = b02_dn_template()
        svc = IncomeStatementService()
        balances = {
            # Revenue: 1000
            "511": {"debit": ZERO, "credit": Decimal(1000)},
            # Sales discounts: 50
            "521": {"debit": Decimal(50), "credit": ZERO},
            # COGS: 400
            "632": {"debit": Decimal(400), "credit": ZERO},
        }
        lines = svc.compute(tmpl, balances)

        # Net revenue = 1000 - 50 = 950
        a_net = next(l for l in lines if l.line_code == "A_NET")
        assert a_net.value_current == Decimal(950)

        # Gross profit = 950 - 400 = 550
        gp = next(l for l in lines if l.line_code == "GROSS_PROFIT")
        assert gp.value_current == Decimal(550)

    def test_empty_balances(self) -> None:
        """All zeros → all lines zero."""
        tmpl = b02_dn_template()
        svc = IncomeStatementService()
        lines = svc.compute(tmpl, {})
        np = next(l for l in lines if l.line_code == "NET_PROFIT")
        assert np.value_current == ZERO

    def test_financial_items(self) -> None:
        """Financial income/expenses computed correctly."""
        tmpl = b02_dn_template()
        engine = ReportEngine()
        balances = {
            "515": {"debit": ZERO, "credit": Decimal(200)},  # Financial income
            "635": {"debit": Decimal(80), "credit": ZERO},  # Financial expenses
        }
        lines = engine.compute(tmpl, balances)

        e = next(l for l in lines if l.line_code == "E")
        assert e.value_current == Decimal(200)  # sign=-1 flip

        f = next(l for l in lines if l.line_code == "F")
        assert f.value_current == Decimal(80)

        nf = next(l for l in lines if l.line_code == "NET_FIN")
        assert nf.value_current == Decimal(120)  # 200 - 80

    def test_other_items(self) -> None:
        """Other income/expenses computed correctly."""
        tmpl = b02_dn_template()
        engine = ReportEngine()
        balances = {
            "711": {"debit": ZERO, "credit": Decimal(50)},  # Other income
            "811": {"debit": Decimal(30), "credit": ZERO},  # Other expenses
        }
        lines = engine.compute(tmpl, balances)

        g = next(l for l in lines if l.line_code == "G")
        assert g.value_current == Decimal(50)  # sign=-1 flip

        h = next(l for l in lines if l.line_code == "H")
        assert h.value_current == Decimal(30)
