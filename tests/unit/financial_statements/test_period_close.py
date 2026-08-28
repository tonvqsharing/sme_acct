"""Unit tests for PeriodCloseService — month-end close logic."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from src.bricks.financial_statements.domain import ClosingEntryType
from src.bricks.financial_statements.services import (
    ACCOUNT_911,
    PeriodAlreadyClosedError,
    PeriodCloseService,
)


class FakePeriodLock:
    """Fake period lock port for testing."""

    def __init__(self) -> None:
        self._locked: dict[tuple[UUID, int, int], bool] = {}

    def is_period_locked(self, company_id: UUID, fiscal_year: int, period: int) -> bool:
        return self._locked.get((company_id, fiscal_year, period), False)

    def lock_period(
        self,
        company_id: UUID,
        fiscal_year: int,
        period: int,
        actor: UUID,
        notes: str | None = None,
    ) -> None:
        self._locked[(company_id, fiscal_year, period)] = True


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


class TestPeriodCloseServiceExpenseTransfer:
    """Tests for expense transfer to 911 (FS-062)."""

    def setup_method(self):
        self.svc = PeriodCloseService()

    def test_single_expense_account(self):
        """One expense account with debit balance → Dr. 6321 / Cr. 911."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(3000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.entry_type == ClosingEntryType.EXPENSE_TRANSFER
        assert result.amount == Decimal(3000000)
        assert len(result.lines) == 2
        assert result.lines[0]["account_code"] == "6321"
        assert result.lines[0]["debit"] == "3000000"
        assert result.lines[1]["account_code"] == ACCOUNT_911
        assert result.lines[1]["credit"] == "3000000"

    def test_multiple_expense_accounts(self):
        """Multiple expense accounts → aggregated into one entry."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(2000000), "credit": Decimal(0)},
            {"account_code": "6351", "debit": Decimal(1000000), "credit": Decimal(0)},
            {"account_code": "6411", "debit": Decimal(500000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(3500000)
        # 3 expense accounts × 2 lines each = 6 lines
        assert len(result.lines) == 6

    def test_expense_with_credit_balance_ignored(self):
        """Expense account with credit balance (refund) → ignored."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(0), "credit": Decimal(1000000)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(0)
        assert len(result.lines) == 0

    def test_expense_with_net_debit(self):
        """Expense account with debit > credit → net amount transferred."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(3000000), "credit": Decimal(500000)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(2500000)

    def test_revenue_accounts_ignored(self):
        """Revenue accounts (5xx) should not appear in expense transfer."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(3000000)},
            {"account_code": "6321", "debit": Decimal(2000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(2000000)
        # Only 6321 should appear (2 lines), not 5111
        codes = [l["account_code"] for l in result.lines]
        assert "5111" not in codes

    def test_financial_expense_711_excluded(self):
        """Account 711 (Financial income) is revenue, not expense."""
        trial_balance = [
            {"account_code": "7111", "debit": Decimal(0), "credit": Decimal(500000)},
            {"account_code": "6321", "debit": Decimal(2000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(2000000)
        codes = [l["account_code"] for l in result.lines]
        assert "7111" not in codes

    def test_financial_expense_712_included(self):
        """Account 712 (Financial expense) is expense type."""
        trial_balance = [
            {"account_code": "7121", "debit": Decimal(800000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(800000)

    def test_cit_expense_8211_included(self):
        """Account 8211 (CIT expense) is expense type."""
        trial_balance = [
            {"account_code": "8211", "debit": Decimal(400000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert result.amount == Decimal(400000)

    def test_empty_trial_balance(self):
        """No accounts → zero amount, no lines."""
        result = self.svc.transfer_expense(
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
            {"account_code": "6321", "debit": Decimal(1000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        assert "7/2026" in result.description
        assert "Chi phí" in result.description

    def test_voucher_lines_are_strings(self):
        """Voucher lines must have string values for VoucherService."""
        trial_balance = [
            {"account_code": "6321", "debit": Decimal(1000000), "credit": Decimal(0)},
        ]
        result = self.svc.transfer_expense(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
        )
        for line in result.lines:
            assert isinstance(line["account_code"], str)
            assert isinstance(line["debit"], str)
            assert isinstance(line["credit"], str)


class TestPeriodCloseServiceCITProvision:
    """Tests for CIT provision (FS-063)."""

    def setup_method(self):
        self.svc = PeriodCloseService()

    def test_positive_net_income(self):
        """Positive net income → CIT provision at 20%."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(10000000),
        )
        assert result is not None
        assert result.entry_type == ClosingEntryType.CIT_PROVISION
        assert result.amount == Decimal(2000000)  # 10M × 20%
        assert len(result.lines) == 2
        assert result.lines[0]["account_code"] == "8211"
        assert result.lines[0]["debit"] == "2000000"
        assert result.lines[1]["account_code"] == "3334"
        assert result.lines[1]["credit"] == "2000000"

    def test_zero_net_income(self):
        """Zero net income → no CIT provision."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(0),
        )
        assert result is None

    def test_negative_net_income(self):
        """Negative net income (loss) → no CIT provision."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(-5000000),
        )
        assert result is None

    def test_custom_cit_rate(self):
        """Custom CIT rate (e.g., preferential 17%)."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(10000000),
            cit_rate=Decimal("0.17"),
        )
        assert result is not None
        assert result.amount == Decimal(1700000)  # 10M × 17%

    def test_cit_rounding(self):
        """CIT amount rounds to nearest integer."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(3333333),
        )
        assert result is not None
        # 3333333 × 0.20 = 666666.6 → rounds to 666667
        assert result.amount == Decimal(666667)

    def test_description_format(self):
        """Description includes period and year."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(5000000),
        )
        assert result is not None
        assert "7/2026" in result.description
        assert "Thuế TNDN" in result.description

    def test_voucher_lines_are_strings(self):
        """Voucher lines must have string values for VoucherService."""
        result = self.svc.calculate_cit_provision(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            net_income=Decimal(5000000),
        )
        assert result is not None
        for line in result.lines:
            assert isinstance(line["account_code"], str)
            assert isinstance(line["debit"], str)
            assert isinstance(line["credit"], str)


class TestPeriodCloseServiceClosePeriod:
    """Tests for close_period orchestrator (FS-064)."""

    def setup_method(self):
        self.lock = FakePeriodLock()
        self.svc = PeriodCloseService(period_lock=self.lock)

    def test_close_period_success(self):
        """Full close: revenue + expense + CIT + lock."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(10000000)},
            {"account_code": "6321", "debit": Decimal(6000000), "credit": Decimal(0)},
        ]
        result = self.svc.close_period(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
            actor=uuid4(),
        )
        assert result.success is True
        assert result.net_income == Decimal(4000000)  # 10M - 6M
        assert len(result.closing_entries) == 3  # revenue + expense + CIT
        # CIT = 4M × 20% = 800000
        cit_entry = result.closing_entries[2]
        assert cit_entry.entry_type == ClosingEntryType.CIT_PROVISION
        assert cit_entry.amount == Decimal(800000)

    def test_close_period_locks_period(self):
        """Close period should lock it."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(5000000)},
        ]
        cid = uuid4()
        self.svc.close_period(
            company_id=cid,
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
            actor=uuid4(),
        )
        assert self.lock.is_period_locked(cid, 2026, 7) is True

    def test_close_period_already_locked(self):
        """Close period raises error if already locked."""
        cid = uuid4()
        self.lock.lock_period(cid, 2026, 7, actor=uuid4())
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(5000000)},
        ]
        import pytest

        with pytest.raises(PeriodAlreadyClosedError):
            self.svc.close_period(
                company_id=cid,
                fiscal_year=2026,
                period=7,
                trial_balance=trial_balance,
                actor=uuid4(),
            )

    def test_close_period_no_lock_port(self):
        """Close period works without lock port (testing mode)."""
        svc = PeriodCloseService(period_lock=None)
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(5000000)},
        ]
        result = svc.close_period(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
            actor=uuid4(),
        )
        assert result.success is True

    def test_close_period_loss_no_cit(self):
        """Close period with loss → no CIT provision."""
        trial_balance = [
            {"account_code": "5111", "debit": Decimal(0), "credit": Decimal(3000000)},
            {"account_code": "6321", "debit": Decimal(5000000), "credit": Decimal(0)},
        ]
        result = self.svc.close_period(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=trial_balance,
            actor=uuid4(),
        )
        assert result.success is True
        assert result.net_income == Decimal(-2000000)  # 3M - 5M
        assert len(result.closing_entries) == 2  # revenue + expense only (no CIT)

    def test_close_period_empty_trial_balance(self):
        """Close period with empty trial balance → zero amounts."""
        result = self.svc.close_period(
            company_id=uuid4(),
            fiscal_year=2026,
            period=7,
            trial_balance=[],
            actor=uuid4(),
        )
        assert result.success is True
        assert result.net_income == Decimal(0)
        assert len(result.closing_entries) == 2  # revenue + expense (both zero)
