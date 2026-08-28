"""Unit tests for PeriodCloseService — month-end close logic."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.bricks.financial_statements.domain import ClosingEntryType
from src.bricks.financial_statements.services import ACCOUNT_911, PeriodCloseService


class TestPeriodCloseServiceRevenueTransfer:
    """Tests for revenue transfer to 911 (FS-061)."""

    def setup_method(self):
        self.svc = PeriodCloseService()

    def test_single_revenue_account(self):
        """One revenue account with credit balance → Dr. 911 / Cr. 5111."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(5000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.entry_type == ClosingEntryType.REVENUE_TRANSFER
        assert result.amount == Decimal(5000000)
        assert len(result.lines) == 2
        assert result.lines[0]["account_code"] == ACCOUNT_911
        assert result.lines[0]["debit"] == "5000000"
        assert result.lines[1]["account_code"] == "5111"
        assert result.lines[1]["credit"] == "5000000"

    def test_multiple_revenue_accounts(self):
        """Multiple revenue accounts → aggregated into one entry."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(3000000)},
            {"account_code": "5112", "debit": Decimal(0), "credit": Decimal(2000000)},
            {"account_code": "5113", "debit": Decimal(0), "credit": Decimal(1000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(6000000)
        # 3 revenue accounts × 2 lines each = 6 lines
        assert len(result.lines) == 6

    def test_revenue_with_debit_balance_ignored(self):
        """Revenue account with debit balance (refund) → ignored."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(1000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(0)
        assert len(result.lines) == 0

    def test_revenue_with_net_credit(self):
        """Revenue account with credit > debit → net amount transferred."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(500000), "credit": Decimal(3000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(2500000)

    def test_expense_accounts_ignored(self):
        """Expense accounts (5xx) should not appear in revenue transfer."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(2000000), "credit": Decimal(0)},
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(3000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(3000000)
        # Only 5111 should appear (2 lines), not 6321
        codes = [l["account_code"] for l in result.lines]
        assert "6321" not in codes

    def test_asset_accounts_ignored(self):
        """Asset accounts (1xx) should not appear in revenue transfer."""
        trial_balance = [
            {"account_code": "111", "debit": Decimal(1000000), "credit": Decimal(0)},
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(3000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(3000000)

    def test_empty_trial_balance(self):
        """No accounts → zero amount, no lines."""
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=[],
        )
        assert result.amount == Decimal(0)
        assert len(result.lines) == 0

    def test_description_format(self):
        """Description includes period and year."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(1000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert "7/2026" in result.description
        assert "Doanh thu" in result.description

    def test_voucher_lines_are_strings(self):
        """Voucher lines must have string values for VoucherService."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(1000000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        for line in result.lines:
            assert isinstance(line["account_code"], str)
            assert isinstance(line["debit"], str)
            assert isinstance(line["credit"], str)

    def test_revenue_711_included(self):
        """Other revenue accounts (711x) are also revenue type."""
        trial_balance = [
            {"account_code": "7111", "debit": Decimal(0), "credit": Decimal(500000)},
        ]
        result = self.svc.transfer_revenue(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        # 7111 starts with "711" → Doanh thu tài chính (Financial income)
        assert result.amount == Decimal(500000)
