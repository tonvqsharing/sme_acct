"""Unit tests for ReportEngine — computation logic."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.financial_statements.domain import (
    LineType,
    ReportTemplate,
    ReportTemplateLine,
)
from src.bricks.financial_statements.services import (
    CircularFormulaError,
    ReportEngine,
    UnknownLineReferenceError,
)

ZERO = Decimal(0)


def _make_template(lines: list[ReportTemplateLine]) -> ReportTemplate:
    return ReportTemplate(code="TEST", name="Test", lines=lines)


def _bal(code: str, debit: str = "0", credit: str = "0") -> tuple[str, dict[str, Decimal]]:
    return code, {"debit": Decimal(debit), "credit": Decimal(credit)}


class TestAccountAggregate:
    """ACCOUNT_AGGREGATE: sum of specified account codes."""

    def test_single_account(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="111",
                    line_name="Cash",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111"],
                )
            ]
        )
        balances = {"1111": {"debit": Decimal(100), "credit": Decimal(30)}}
        result = engine.compute(tmpl, balances)
        assert len(result) == 1
        assert result[0].value_current == Decimal(70)  # 100 - 30

    def test_multiple_accounts(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="100",
                    line_name="Cash and equivalents",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111", "1112", "1113"],
                )
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "1112": {"debit": Decimal(200), "credit": Decimal(50)},
            "1113": {"debit": ZERO, "credit": Decimal(30)},
        }
        result = engine.compute(tmpl, balances)
        # (100-0) + (200-50) + (0-30) = 100 + 150 - 30 = 220
        assert result[0].value_current == Decimal(220)

    def test_missing_account_ignored(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="100",
                    line_name="Cash",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111", "9999"],  # 9999 doesn't exist
                )
            ]
        )
        balances = {"1111": {"debit": Decimal(100), "credit": ZERO}}
        result = engine.compute(tmpl, balances)
        assert result[0].value_current == Decimal(100)

    def test_sign_negative(self) -> None:
        """sign=-1 flips the direction (for contra accounts)."""
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="511",
                    line_name="Revenue",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["5111"],
                    sign=-1,
                )
            ]
        )
        balances = {"5111": {"debit": Decimal(10), "credit": Decimal(500)}}
        result = engine.compute(tmpl, balances)
        # (10 - 500) * -1 = -490 * -1 = 490
        assert result[0].value_current == Decimal(490)

    def test_empty_account_codes(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="100",
                    line_name="Empty",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=[],
                )
            ]
        )
        result = engine.compute(tmpl, {})
        assert result[0].value_current == ZERO


class TestHeader:
    """HEADER lines return zero."""

    def test_header_returns_zero(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="A",
                    line_name="Section A",
                    line_type=LineType.HEADER,
                )
            ]
        )
        result = engine.compute(tmpl, {})
        assert result[0].value_current == ZERO


class TestTotal:
    """TOTAL: sum of child lines."""

    def test_sum_children(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="100",
                    line_name="Cash and equivalents",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111"],
                    parent_code="TOTAL",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="110",
                    line_name="Bank",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1121"],
                    parent_code="TOTAL",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="TOTAL",
                    line_name="Total Cash",
                    line_type=LineType.TOTAL,
                ),
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "1121": {"debit": Decimal(200), "credit": Decimal(50)},
        }
        result = engine.compute(tmpl, balances)
        total_line = next(r for r in result if r.line_code == "TOTAL")
        # 100 + 150 = 250
        assert total_line.value_current == Decimal(250)

    def test_no_children_returns_zero(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="EMPTY",
                    line_name="Empty Total",
                    line_type=LineType.TOTAL,
                )
            ]
        )
        result = engine.compute(tmpl, {})
        assert result[0].value_current == ZERO

    def test_nested_totals(self) -> None:
        """TOTAL of TOTALs."""
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="111",
                    line_name="Cash",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111"],
                    parent_code="SHORT",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="SHORT",
                    line_name="Short-term",
                    line_type=LineType.TOTAL,
                    parent_code="GRAND",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="211",
                    line_name="Fixed",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["2111"],
                    parent_code="LONG",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="LONG",
                    line_name="Long-term",
                    line_type=LineType.TOTAL,
                    parent_code="GRAND",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="GRAND",
                    line_name="Grand Total",
                    line_type=LineType.TOTAL,
                ),
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "2111": {"debit": Decimal(500), "credit": Decimal(100)},
        }
        result = engine.compute(tmpl, balances)
        grand = next(r for r in result if r.line_code == "GRAND")
        # SHORT=100, LONG=400, GRAND=100+400=500
        assert grand.value_current == Decimal(500)


class TestFormula:
    """FORMULA: arithmetic on other lines."""

    def test_simple_add(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="A",
                    line_name="Line A",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="B",
                    line_name="Line B",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1121"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="C",
                    line_name="A + B",
                    line_type=LineType.FORMULA,
                    formula="A+B",
                ),
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "1121": {"debit": Decimal(200), "credit": ZERO},
        }
        result = engine.compute(tmpl, balances)
        c_line = next(r for r in result if r.line_code == "C")
        assert c_line.value_current == Decimal(300)

    def test_subtract(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="A",
                    line_name="Revenue",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["5111"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="B",
                    line_name="COGS",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["6321"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="C",
                    line_name="Gross Profit",
                    line_type=LineType.FORMULA,
                    formula="A-B",
                ),
            ]
        )
        balances = {
            "5111": {"debit": ZERO, "credit": Decimal(1000)},
            "6321": {"debit": Decimal(600), "credit": ZERO},
        }
        result = engine.compute(tmpl, balances)
        c_line = next(r for r in result if r.line_code == "C")
        # A = 0-1000 = -1000, B = 600-0 = 600, A-B = -1600
        assert c_line.value_current == Decimal(-1600)

    def test_mixed_operations(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="A",
                    line_name="A",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="B",
                    line_name="B",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1121"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="C",
                    line_name="C",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1131"],
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="RESULT",
                    line_name="A+B-C",
                    line_type=LineType.FORMULA,
                    formula="A+B-C",
                ),
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "1121": {"debit": Decimal(200), "credit": ZERO},
            "1131": {"debit": Decimal(50), "credit": ZERO},
        }
        result = engine.compute(tmpl, balances)
        r = next(x for x in result if x.line_code == "RESULT")
        assert r.value_current == Decimal(250)  # 100+200-50

    def test_unknown_reference_raises(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="X",
                    line_name="X",
                    line_type=LineType.FORMULA,
                    formula="A+B",
                )
            ]
        )
        with pytest.raises(UnknownLineReferenceError, match="unknown line 'A'"):
            engine.compute(tmpl, {})

    def test_empty_formula_returns_zero(self) -> None:
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="X",
                    line_name="X",
                    line_type=LineType.FORMULA,
                    formula=None,
                )
            ]
        )
        result = engine.compute(tmpl, {})
        assert result[0].value_current == ZERO

    def test_circular_reference_raises(self) -> None:
        """Formula A references B, B references A → CircularFormulaError."""
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="A",
                    line_name="A",
                    line_type=LineType.FORMULA,
                    formula="B+1",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="B",
                    line_name="B",
                    line_type=LineType.FORMULA,
                    formula="A+1",
                ),
            ]
        )
        with pytest.raises(CircularFormulaError, match="Circular reference"):
            engine.compute(tmpl, {})

    def test_self_reference_raises(self) -> None:
        """Formula references itself."""
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="X",
                    line_name="X",
                    line_type=LineType.FORMULA,
                    formula="X+1",
                )
            ]
        )
        with pytest.raises(CircularFormulaError, match="Circular reference"):
            engine.compute(tmpl, {})


class TestIntegration:
    """End-to-end scenarios."""

    def test_trial_balance_style(self) -> None:
        """Simulate S06-DN style: groups of accounts + totals."""
        engine = ReportEngine()
        tmpl = _make_template(
            [
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="111",
                    line_name="Cash",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1111", "1112"],
                    parent_code="ASSETS",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="131",
                    line_name="Receivables",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["1311"],
                    parent_code="ASSETS",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="ASSETS",
                    line_name="Total Assets",
                    line_type=LineType.TOTAL,
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="211",
                    line_name="Payables",
                    line_type=LineType.ACCOUNT_AGGREGATE,
                    account_codes=["2111"],
                    parent_code="LIAB",
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="LIAB",
                    line_name="Total Liabilities",
                    line_type=LineType.TOTAL,
                ),
                ReportTemplateLine(
                    template_id=uuid4(),
                    line_code="CHECK",
                    line_name="Balance Check",
                    line_type=LineType.FORMULA,
                    formula="ASSETS-LIAB",
                ),
            ]
        )
        balances = {
            "1111": {"debit": Decimal(100), "credit": ZERO},
            "1112": {"debit": Decimal(200), "credit": ZERO},
            "1311": {"debit": Decimal(50), "credit": ZERO},
            "2111": {"debit": ZERO, "credit": Decimal(350)},
        }
        result = engine.compute(tmpl, balances)
        assets = next(r for r in result if r.line_code == "ASSETS")
        liab = next(r for r in result if r.line_code == "LIAB")
        check = next(r for r in result if r.line_code == "CHECK")

        # ASSETS: (100+200) + 50 = 350
        assert assets.value_current == Decimal(350)
        # LIAB: (0 - 350) = -350
        assert liab.value_current == Decimal(-350)
        # CHECK: 350 - (-350) = 700
        assert check.value_current == Decimal(700)
