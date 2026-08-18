"""Unit tests for Currencies & Exchange Rates domain entities.

Covers Currency, ExchangeRate, RevaluationRun/Entry value objects per
docs/currencies-exchange/rules-currencies.md (D1-D9) and specs §2.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.base import PostingSide, RateType, RevaluationStatus
from src.domain.entities.currency import (
    Currency,
    ExchangeRate,
    FXDifference,
    RevaluationEntry,
    RevaluationRun,
)
from src.domain.exceptions import (
    InvalidCurrencyError,
    InvalidRateError,
    RevaluationError,
)

# ── Currency ────────────────────────────────────────────────────────────────


class TestCurrency:
    def test_valid_currency(self):
        c = Currency(code="USD", name="US Dollar", symbol="$")
        assert c.code == "USD"
        assert c.decimal_places == 2
        assert c.is_active is True
        assert c.is_base is False

    def test_code_must_be_3_uppercase_letters(self):
        with pytest.raises(InvalidCurrencyError):
            Currency(code="usd", name="US Dollar", symbol="$")
        with pytest.raises(InvalidCurrencyError):
            Currency(code="US", name="US Dollar", symbol="$")
        with pytest.raises(InvalidCurrencyError):
            Currency(code="US1", name="US Dollar", symbol="$")

    def test_vnd_defaults(self):
        c = Currency(code="VND", name="Đồng Việt Nam", symbol="₫", decimal_places=0)
        assert c.decimal_places == 0
        assert c.display_format == "{symbol} {amount:,.2f}"


# ── ExchangeRate ────────────────────────────────────────────────────────────


class TestExchangeRate:
    def test_valid_rate(self):
        r = ExchangeRate(
            currency_code="USD",
            rate_date=date(2026, 8, 1),
            rate_type=RateType.BUY,
            rate=Decimal("24700"),
            source="MANUAL",
            actor=uuid4(),
        )
        assert r.rate == Decimal("24700")
        assert r.note is None

    def test_rate_must_be_positive(self):
        with pytest.raises(InvalidRateError):
            ExchangeRate(
                currency_code="USD",
                rate_date=date(2026, 8, 1),
                rate_type=RateType.BUY,
                rate=Decimal("0"),
                source="MANUAL",
                actor=uuid4(),
            )
        with pytest.raises(InvalidRateError):
            ExchangeRate(
                currency_code="USD",
                rate_date=date(2026, 8, 1),
                rate_type=RateType.BUY,
                rate=Decimal("-100"),
                source="MANUAL",
                actor=uuid4(),
            )

    def test_invalid_currency_code_rejected(self):
        with pytest.raises(InvalidCurrencyError):
            ExchangeRate(
                currency_code="usd",
                rate_date=date(2026, 8, 1),
                rate_type=RateType.BUY,
                rate=Decimal("24700"),
                source="MANUAL",
                actor=uuid4(),
            )


# ── RevaluationRun / Entry ──────────────────────────────────────────────────


def _entry(
    account_code="1122",
    currency_code="USD",
    balance=Decimal("1000"),
    rate=Decimal("24700"),
    old_vnd=Decimal("24000000"),
) -> RevaluationEntry:
    return RevaluationEntry(
        account_code=account_code,
        currency_code=currency_code,
        balance_original=balance,
        rate_applied=rate,
        old_vnd=old_vnd,
        new_vnd=balance * rate,
        difference=balance * rate - old_vnd,
    )


class TestRevaluationEntry:
    def test_difference_computed(self):
        e = _entry(balance=Decimal("1000"), rate=Decimal("24700"), old_vnd=Decimal("24000000"))
        assert e.new_vnd == Decimal("24700000")
        assert e.difference == Decimal("700000")

    def test_posting_side_default(self):
        e = _entry()
        assert e.posting_side is None  # derived at run level


class TestRevaluationRun:
    def _run(self):
        return RevaluationRun(
            company_id=uuid4(),
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=uuid4(),
        )

    def test_new_run_is_draft(self):
        run = self._run()
        assert run.status == RevaluationStatus.DRAFT
        assert run.entries == []
        assert run.approver is None
        assert run.posted_at is None

    def test_approval_chain_draft_to_approved(self):
        run = self._run()
        run.submit_for_approval()
        assert run.status == RevaluationStatus.PENDING_APPROVAL
        approver = uuid4()
        run.approve(approver)
        assert run.status == RevaluationStatus.APPROVED
        assert run.approver == approver

    def test_cannot_approve_without_pending(self):
        run = self._run()
        with pytest.raises(RevaluationError):
            run.approve(uuid4())

    def test_post_requires_approved_and_balanced(self):
        run = self._run()
        # gain entry + offsetting credit → balanced
        gain = _entry(
            account_code="1122",
            balance=Decimal("1000"),
            rate=Decimal("24700"),
            old_vnd=Decimal("24000000"),
        )
        offset = RevaluationEntry(
            account_code="5151",
            currency_code="USD",
            balance_original=Decimal("0"),
            rate_applied=Decimal("24700"),
            old_vnd=Decimal("0"),
            new_vnd=Decimal("0"),
            difference=Decimal("-700000"),
            posting_side=PostingSide.CREDIT,
        )
        run.entries = [gain, offset]
        run.submit_for_approval()
        run.approve(uuid4())
        run.post()
        assert run.status == RevaluationStatus.POSTED
        assert run.posted_at is not None

    def test_unbalanced_postings_rejected(self):
        run = self._run()
        run.entries = [_entry()]
        run.submit_for_approval()
        run.approve(uuid4())
        with pytest.raises(RevaluationError):
            run.post()

    def test_reverse_only_when_posted(self):
        run = self._run()
        with pytest.raises(RevaluationError):
            run.reverse()
        run.entries = [_entry()]
        run.status = RevaluationStatus.POSTED
        run.reverse()
        assert run.status == RevaluationStatus.REVERSED


# ── FXDifference (report row) ───────────────────────────────────────────────


class TestFXDifference:
    def test_report_row_holds_balances(self):
        d = FXDifference(
            company_id=uuid4(),
            account_code="1122",
            currency_code="USD",
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            opening_original=Decimal("1000"),
            opening_vnd=Decimal("24000000"),
            movements_original=Decimal("0"),
            movements_vnd=Decimal("0"),
            closing_original=Decimal("1000"),
            closing_vnd=Decimal("24000000"),
            revaluation_adjustment=Decimal("700000"),
            cumulative_difference=Decimal("700000"),
        )
        assert d.closing_vnd + d.revaluation_adjustment == Decimal("24700000")
