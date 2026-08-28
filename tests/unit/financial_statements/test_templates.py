"""Tests for B01-DN Balance Sheet template."""

from __future__ import annotations

from src.bricks.financial_statements.domain import LineType
from src.bricks.financial_statements.templates import b01_dn_template


class TestB01DNTemplate:
    """B01-DN template structure."""

    def test_template_code(self) -> None:
        tmpl = b01_dn_template()
        assert tmpl.code == "B01-DN"
        assert tmpl.name == "Bảng cân đối kế toán"

    def test_has_all_sections(self) -> None:
        tmpl = b01_dn_template()
        codes = {line.line_code for line in tmpl.lines}
        # Headers
        assert "A" in codes  # Short-term assets
        assert "B" in codes  # Long-term assets
        assert "C" in codes  # Liabilities
        assert "D" in codes  # Equity
        # Totals
        assert "A_TONG" in codes
        assert "B_TONG" in codes
        assert "TS_TONG" in codes
        assert "C_TONG" in codes
        assert "D_TONG" in codes
        assert "NNC_TONG" in codes
        # Balance check
        assert "CHECK" in codes

    def test_balance_check_formula(self) -> None:
        tmpl = b01_dn_template()
        check = next(l for l in tmpl.lines if l.line_code == "CHECK")
        assert check.formula == "TS_TONG-NNC_TONG"
        assert check.line_type == LineType.FORMULA

    def test_total_assets_formula(self) -> None:
        tmpl = b01_dn_template()
        ts = next(l for l in tmpl.lines if l.line_code == "TS_TONG")
        assert ts.formula == "A_TONG+B_TONG"

    def test_total_liab_equity_formula(self) -> None:
        tmpl = b01_dn_template()
        nnc = next(l for l in tmpl.lines if l.line_code == "NNC_TONG")
        assert nnc.formula == "C_TONG+D_TONG"

    def test_short_term_assets_have_children(self) -> None:
        tmpl = b01_dn_template()
        a_children = [l for l in tmpl.lines if l.parent_code == "A_TONG"]
        assert len(a_children) >= 5  # A1-A5

    def test_long_term_assets_have_children(self) -> None:
        tmpl = b01_dn_template()
        b_children = [l for l in tmpl.lines if l.parent_code == "B_TONG"]
        assert len(b_children) >= 5  # B1-B6

    def test_liabilities_have_children(self) -> None:
        tmpl = b01_dn_template()
        c_children = [l for l in tmpl.lines if l.parent_code == "C_TONG"]
        assert len(c_children) >= 2  # C1-C2

    def test_equity_have_children(self) -> None:
        tmpl = b01_dn_template()
        d_children = [l for l in tmpl.lines if l.parent_code == "D_TONG"]
        assert len(d_children) >= 4  # D1-D4
