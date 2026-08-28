"""Tests for account type classification — TT99 Appendix II."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.coa.domain import (
    Account,
    AccountType,
    classify_account,
)


class TestAccountType:
    """AccountType enum values."""

    def test_asset_value(self) -> None:
        assert AccountType.ASSET.value == "asset"

    def test_liability_value(self) -> None:
        assert AccountType.LIABILITY.value == "liability"

    def test_equity_value(self) -> None:
        assert AccountType.EQUITY.value == "equity"

    def test_revenue_value(self) -> None:
        assert AccountType.REVENUE.value == "revenue"

    def test_expense_value(self) -> None:
        assert AccountType.EXPENSE.value == "expense"

    def test_all_types_covered(self) -> None:
        types = {t.value for t in AccountType}
        assert types == {"asset", "liability", "equity", "revenue", "expense"}


class TestClassifyAccount:
    """classify_account() function — auto-classify by first digit."""

    def test_asset_1xx(self) -> None:
        assert classify_account("111") == AccountType.ASSET
        assert classify_account("1121") == AccountType.ASSET
        assert classify_account("1311") == AccountType.ASSET
        assert classify_account("154") == AccountType.ASSET

    def test_liability_2xx(self) -> None:
        assert classify_account("211") == AccountType.LIABILITY
        assert classify_account("221") == AccountType.LIABILITY

    def test_equity_3xx(self) -> None:
        assert classify_account("311") == AccountType.EQUITY
        assert classify_account("3331") == AccountType.EQUITY

    def test_revenue_4xx(self) -> None:
        assert classify_account("411") == AccountType.REVENUE
        assert classify_account("412") == AccountType.REVENUE
        assert classify_account("511") == AccountType.EXPENSE

    def test_expense_5xx(self) -> None:
        assert classify_account("511") == AccountType.EXPENSE
        assert classify_account("512") == AccountType.EXPENSE

    def test_tt99_long_codes(self) -> None:
        """TT99 uses 10-digit codes — first digit still determines type."""
        assert classify_account("1110000001") == AccountType.ASSET
        assert classify_account("3331100001") == AccountType.EQUITY
        assert classify_account("4111000001") == AccountType.REVENUE
        assert classify_account("5111000001") == AccountType.EXPENSE

    def test_invalid_code_no_digit(self) -> None:
        with pytest.raises(ValueError, match="must start with digit"):
            classify_account("abc")

    def test_invalid_code_zero_start(self) -> None:
        with pytest.raises(ValueError, match="must be 1-5"):
            classify_account("011")

    def test_invalid_code_digit_6_plus(self) -> None:
        """Codes starting with 6-9 are valid in TT133 (mapped to EXPENSE)."""
        assert classify_account("611") == AccountType.EXPENSE
        assert classify_account("711") == AccountType.EXPENSE
        assert classify_account("811") == AccountType.EXPENSE
        assert classify_account("911") == AccountType.EXPENSE


class TestAccountDomain:
    """Account dataclass with account_type field."""

    def test_account_has_account_type(self) -> None:
        acc = Account(
            company_id=uuid4(),
            code="111",
            name="Cash",
            account_type=AccountType.ASSET,
        )
        assert acc.account_type == AccountType.ASSET

    def test_account_auto_classifies(self) -> None:
        """Account auto-classifies if account_type not provided."""
        acc = Account(
            company_id=uuid4(),
            code="411",
            name="Capital",
        )
        assert acc.account_type == AccountType.REVENUE

    def test_account_explicit_overrides_auto(self) -> None:
        """Explicit account_type overrides auto-classification."""
        acc = Account(
            company_id=uuid4(),
            code="111",
            name="Cash",
            account_type=AccountType.ASSET,
        )
        assert acc.account_type == AccountType.ASSET

    def test_account_is_detail_unchanged(self) -> None:
        """is_detail property still works with account_type."""
        agg = Account(company_id=uuid4(), code="111", name="Cash aggregate")
        detail = Account(company_id=uuid4(), code="1111", name="Cash detail")
        assert agg.is_detail is False
        assert detail.is_detail is True

    def test_account_tt133_types(self) -> None:
        """TT133 accounts get correct types."""
        asset = Account(company_id=uuid4(), code="111", name="Cash")
        liability = Account(company_id=uuid4(), code="211", name="Payable")
        equity = Account(company_id=uuid4(), code="311", name="Capital")
        revenue = Account(company_id=uuid4(), code="411", name="Capital")
        expense = Account(company_id=uuid4(), code="511", name="Revenue")

        assert asset.account_type == AccountType.ASSET
        assert liability.account_type == AccountType.LIABILITY
        assert equity.account_type == AccountType.EQUITY
        assert revenue.account_type == AccountType.REVENUE
        assert expense.account_type == AccountType.EXPENSE
