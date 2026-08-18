"""Unit tests for currency + exchange rate + revaluation services.

Mock repository ports. Covers rules-currencies.md D1-D9 and
specs-currencies.md §3 (booking rate), §4 (revaluation), §7 (CSV import).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.application.services.currency_service import CurrencyService
from src.application.services.exchange_rate_service import ExchangeRateService
from src.application.services.revaluation_service import RevaluationService
from src.domain.entities.base import PostingSide, RateType, RevaluationStatus
from src.domain.entities.currency import Currency, ExchangeRate, RevaluationEntry, RevaluationRun
from src.domain.exceptions import (
    CurrencyNotFoundError,
    FXImportError,
    InvalidCurrencyError,
    InvalidRateError,
    PeriodLockedError,
    RateNotFoundError,
    RevaluationError,
)

FIXED_ACTOR = uuid4()
FIXED_COMPANY = uuid4()


# ── CurrencyService ─────────────────────────────────────────────────────────


class TestCurrencyService:
    def _service(self, repo=None):
        return CurrencyService(currency_repo=repo or MagicMock())

    def test_create_currency_saves(self):
        repo = MagicMock()
        repo.exists.return_value = False
        svc = self._service(repo)
        cur = Currency(code="USD", name="US Dollar", symbol="$")
        svc.create_currency(cur)
        repo.save.assert_called_once_with(cur)

    def test_duplicate_currency_rejected(self):
        repo = MagicMock()
        repo.exists.return_value = True
        svc = self._service(repo)
        with pytest.raises(InvalidCurrencyError):
            svc.create_currency(Currency(code="USD", name="US Dollar", symbol="$"))

    def test_invalid_code_rejected(self):
        svc = self._service()
        with pytest.raises(InvalidCurrencyError):
            svc.create_currency(Currency(code="usd", name="US Dollar", symbol="$"))

    def test_deactivate_missing_currency(self):
        repo = MagicMock()
        repo.get.return_value = None
        svc = self._service(repo)
        with pytest.raises(CurrencyNotFoundError):
            svc.deactivate_currency("USD", actor=FIXED_ACTOR)

    def test_deactivate_base_currency_blocked(self):
        repo = MagicMock()
        repo.get.return_value = Currency(code="VND", name="Đồng", symbol="₫", is_base=True)
        svc = self._service(repo)
        with pytest.raises(InvalidCurrencyError):
            svc.deactivate_currency("VND", actor=FIXED_ACTOR)

    def test_update_base_flag_blocked(self):
        """D4: is_base immutable — PATCH cannot flip base on/off."""
        repo = MagicMock()
        repo.get.return_value = Currency(code="VND", name="Đồng", symbol="₫", is_base=True)
        svc = self._service(repo)
        with pytest.raises(InvalidCurrencyError):
            svc.update_currency(Currency(code="VND", name="Đồng", symbol="₫", is_base=False))

    def test_create_second_base_blocked(self):
        """D4: only one base currency allowed."""
        repo = MagicMock()
        repo.exists.return_value = False
        repo.list_active.return_value = [
            Currency(code="VND", name="Đồng", symbol="₫", is_base=True)
        ]
        svc = self._service(repo)
        with pytest.raises(InvalidCurrencyError):
            svc.create_currency(Currency(code="USD", name="US Dollar", symbol="$", is_base=True))


# ── ExchangeRateService ─────────────────────────────────────────────────────


class TestExchangeRateService:
    def _service(self, rate_repo=None, cur_repo=None):
        return ExchangeRateService(
            rate_repo=rate_repo or MagicMock(),
            currency_repo=cur_repo or MagicMock(),
        )

    def test_create_rate_valid(self):
        rate_repo = MagicMock()
        rate_repo.create.side_effect = lambda r: r
        cur_repo = MagicMock()
        cur_repo.exists.return_value = True
        svc = self._service(rate_repo, cur_repo)
        rate = svc.create_rate(
            currency_code="USD",
            rate_date=date(2026, 8, 1),
            rate_type=RateType.BUY,
            rate="24700",
            source="MANUAL",
            actor=FIXED_ACTOR,
        )
        assert rate.rate == Decimal("24700")
        rate_repo.create.assert_called_once()

    def test_create_rate_unknown_currency(self):
        cur_repo = MagicMock()
        cur_repo.exists.return_value = False
        svc = self._service(cur_repo=cur_repo)
        with pytest.raises(CurrencyNotFoundError):
            svc.create_rate("USD", date(2026, 8, 1), RateType.BUY, "24700", "MANUAL", FIXED_ACTOR)

    def test_create_rate_non_positive_rejected(self):
        cur_repo = MagicMock()
        cur_repo.exists.return_value = True
        svc = self._service(cur_repo=cur_repo)
        with pytest.raises(InvalidRateError):
            svc.create_rate("USD", date(2026, 8, 1), RateType.BUY, "0", "MANUAL", FIXED_ACTOR)

    def test_resolve_debit_uses_actual_rate(self):
        """R1: Nợ side → tỷ giá giao dịch thực tế."""
        rate_repo = MagicMock()
        svc = self._service(rate_repo=rate_repo)
        got = svc.resolve_booking_rate(
            entry_side=PostingSide.DEBIT,
            currency_code="USD",
            rate_date=date(2026, 8, 5),
            actual_rate=Decimal("24700"),
        )
        assert got == Decimal("24700")
        rate_repo.get_latest.assert_not_called()

    def test_resolve_debit_falls_back_to_latest(self):
        """No actual rate → last available rate ≤ date."""
        rate_repo = MagicMock()
        rate_repo.get_latest.return_value = ExchangeRate(
            currency_code="USD",
            rate_date=date(2026, 8, 1),
            rate_type=RateType.BUY,
            rate=Decimal("24600"),
            source="MANUAL",
            actor=FIXED_ACTOR,
        )
        svc = self._service(rate_repo=rate_repo)
        got = svc.resolve_booking_rate(
            entry_side=PostingSide.DEBIT, currency_code="USD", rate_date=date(2026, 8, 5)
        )
        assert got == Decimal("24600")

    def test_resolve_debit_no_rate_raises(self):
        rate_repo = MagicMock()
        rate_repo.get_latest.return_value = None
        svc = self._service(rate_repo=rate_repo)
        with pytest.raises(RateNotFoundError):
            svc.resolve_booking_rate(
                entry_side=PostingSide.DEBIT, currency_code="USD", rate_date=date(2026, 8, 5)
            )

    def test_resolve_credit_weighted_average(self):
        """R1/D5: Có side → bình quân gia quyền Σ(amt×rate)/Σ(amt)."""
        rate_repo = MagicMock()
        svc = self._service(rate_repo=rate_repo)
        open_balance = [
            (Decimal("1000"), Decimal("24000")),
            (Decimal("1000"), Decimal("26000")),
        ]
        got = svc.resolve_booking_rate(
            entry_side=PostingSide.CREDIT,
            currency_code="USD",
            rate_date=date(2026, 8, 5),
            open_fx_balance=open_balance,
        )
        # (1000*24000 + 1000*26000)/2000 = 25000
        assert got == Decimal("25000")

    def test_resolve_credit_empty_balance_uses_actual(self):
        svc = self._service()
        got = svc.resolve_booking_rate(
            entry_side=PostingSide.CREDIT,
            currency_code="USD",
            rate_date=date(2026, 8, 5),
            actual_rate=Decimal("24700"),
            open_fx_balance=[],
        )
        assert got == Decimal("24700")

    def test_import_csv_atomic(self):
        """§7: valid rows applied only if all rows valid (default atomic)."""
        cur_repo = MagicMock()
        cur_repo.exists.return_value = True
        rate_repo = MagicMock()
        svc = self._service(rate_repo, cur_repo)
        csv_content = (
            "rate_date,currency,rate_type,rate,source,note\n"
            "2026-08-01,USD,BUY,24700,CSV_IMPORT,aug\n"
            "2026-08-01,USD,SELL,24900,CSV_IMPORT,aug\n"
        )
        result = svc.import_csv(csv_content, actor=FIXED_ACTOR)
        assert result["imported"] == 2
        assert result["errors"] == []
        assert rate_repo.create.call_count == 2

    def test_import_csv_rejects_bad_row(self):
        cur_repo = MagicMock()
        cur_repo.exists.return_value = True
        rate_repo = MagicMock()
        svc = self._service(rate_repo, cur_repo)
        csv_content = (
            "rate_date,currency,rate_type,rate,source,note\n"
            "2026-08-01,USD,BUY,0,CSV_IMPORT,bad rate\n"
            "2026-08-01,USD,SELL,24900,CSV_IMPORT,ok\n"
        )
        with pytest.raises(FXImportError):
            svc.import_csv(csv_content, actor=FIXED_ACTOR)
        rate_repo.create.assert_not_called()

    def test_import_csv_unknown_currency(self):
        cur_repo = MagicMock()
        cur_repo.exists.side_effect = lambda code: code == "USD"
        svc = self._service(cur_repo=cur_repo)
        csv_content = (
            "rate_date,currency,rate_type,rate,source,note\n"
            "2026-08-01,XXX,BUY,100,CSV_IMPORT,bad currency\n"
        )
        with pytest.raises(FXImportError):
            svc.import_csv(csv_content, actor=FIXED_ACTOR)

    def test_import_csv_duplicate_rows_rejected(self):
        """§7 atomic: duplicate (currency, rate_date, rate_type) rows must
        fail validation — otherwise first row commits and second hits the
        DB unique constraint → partial import."""
        cur_repo = MagicMock()
        cur_repo.exists.return_value = True
        rate_repo = MagicMock()
        svc = self._service(rate_repo, cur_repo)
        csv_content = (
            "rate_date,currency,rate_type,rate,source,note\n"
            "2026-08-01,USD,BUY,24700,CSV_IMPORT,first\n"
            "2026-08-01,USD,BUY,24800,CSV_IMPORT,duplicate\n"
        )
        with pytest.raises(FXImportError):
            svc.import_csv(csv_content, actor=FIXED_ACTOR)
        rate_repo.create.assert_not_called()


# ── RevaluationService ──────────────────────────────────────────────────────

MONETARY_ITEMS = [
    {
        "account_code": "1122",
        "currency_code": "USD",
        "balance_original": Decimal("1000"),
        "old_vnd": Decimal("24000000"),
    }
]


class TestRevaluationService:
    def _service(self, reval_repo=None, rate_repo=None):
        return RevaluationService(
            revaluation_repo=reval_repo or MagicMock(),
            rate_repo=rate_repo or MagicMock(),
        )

    def _rate_repo_with_rate(self, rate=Decimal("24700")):
        rate_repo = MagicMock()
        rate_repo.get_latest.return_value = ExchangeRate(
            currency_code="USD",
            rate_date=date(2026, 8, 31),
            rate_type=RateType.TRANSFER,
            rate=rate,
            source="MANUAL",
            actor=FIXED_ACTOR,
        )
        return rate_repo

    def test_create_run_computes_entries(self):
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        reval_repo.get_posted_run.return_value = None
        reval_repo.create_run.side_effect = lambda run: run
        svc = self._service(reval_repo, self._rate_repo_with_rate())
        run = svc.create_run(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            monetary_items=MONETARY_ITEMS,
            actor=FIXED_ACTOR,
        )
        # gain 700,000 on 1122 (debit side) + offset credit on 515 (gain acct)
        gains = [e for e in run.entries if e.difference > 0]
        offsets = [e for e in run.entries if e.difference < 0]
        assert len(gains) == 1
        assert gains[0].account_code == "1122"
        assert gains[0].difference == Decimal("700000")
        assert len(offsets) == 1
        assert offsets[0].account_code == "5151"
        # balanced (D6)
        assert abs(sum(e.difference for e in run.entries)) < Decimal("0.01")

    def test_create_run_loss_posts_to_635(self):
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        reval_repo.get_posted_run.return_value = None
        reval_repo.create_run.side_effect = lambda run: run
        svc = self._service(reval_repo, self._rate_repo_with_rate(Decimal("23000")))
        run = svc.create_run(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            monetary_items=MONETARY_ITEMS,
            actor=FIXED_ACTOR,
        )
        # loss: 1000*23000 - 24000000 = -1,000,000 → 635 debit
        losses = [e for e in run.entries if e.difference < 0]
        offset_credits = [e for e in run.entries if e.difference > 0]
        assert losses[0].account_code == "1122"
        assert losses[0].difference == Decimal("-1000000")
        assert offset_credits[0].account_code == "6351"

    def test_create_run_period_locked(self):
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = True
        svc = self._service(reval_repo)
        with pytest.raises(PeriodLockedError):
            svc.create_run(
                company_id=FIXED_COMPANY,
                period_start=date(2026, 8, 1),
                period_end=date(2026, 8, 31),
                rate_date=date(2026, 8, 31),
                monetary_items=MONETARY_ITEMS,
                actor=FIXED_ACTOR,
            )

    def test_create_run_no_closing_rate(self):
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        reval_repo.get_posted_run.return_value = None
        rate_repo = MagicMock()
        rate_repo.get_latest.return_value = None
        svc = self._service(reval_repo, rate_repo)
        with pytest.raises(RateNotFoundError):
            svc.create_run(
                company_id=FIXED_COMPANY,
                period_start=date(2026, 8, 1),
                period_end=date(2026, 8, 31),
                rate_date=date(2026, 8, 31),
                monetary_items=MONETARY_ITEMS,
                actor=FIXED_ACTOR,
            )

    def test_create_run_reverses_prior_posted(self):
        """D7 idempotent re-run: prior POSTED run reversed first."""
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        prior = RevaluationRun(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
            status=RevaluationStatus.POSTED,
        )
        reval_repo.get_posted_run.return_value = prior
        reval_repo.create_run.side_effect = lambda run: run
        svc = self._service(reval_repo, self._rate_repo_with_rate())
        svc.create_run(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            monetary_items=MONETARY_ITEMS,
            actor=FIXED_ACTOR,
        )
        assert prior.status == RevaluationStatus.REVERSED
        reval_repo.save_run.assert_called_with(prior)

    def test_create_run_no_reverse_when_new_run_fails(self):
        """D7 safety: failed new run must NOT destroy prior POSTED run."""
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        prior = RevaluationRun(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
            status=RevaluationStatus.POSTED,
        )
        reval_repo.get_posted_run.return_value = prior
        rate_repo = MagicMock()
        rate_repo.get_latest.return_value = None  # no closing rate → new run fails
        svc = self._service(reval_repo, rate_repo)
        with pytest.raises(RateNotFoundError):
            svc.create_run(
                company_id=FIXED_COMPANY,
                period_start=date(2026, 8, 1),
                period_end=date(2026, 8, 31),
                rate_date=date(2026, 8, 31),
                monetary_items=MONETARY_ITEMS,
                actor=FIXED_ACTOR,
            )
        # prior run must remain POSTED — nothing reversed, nothing saved
        assert prior.status == RevaluationStatus.POSTED
        reval_repo.save_run.assert_not_called()

    def test_create_run_malformed_item_raises_value_error(self):
        """Missing monetary_item key → ValueError (API maps to 400), not KeyError."""
        reval_repo = MagicMock()
        reval_repo.period_is_locked.return_value = False
        reval_repo.get_posted_run.return_value = None
        svc = self._service(reval_repo, self._rate_repo_with_rate())
        with pytest.raises(ValueError):
            svc.create_run(
                company_id=FIXED_COMPANY,
                period_start=date(2026, 8, 1),
                period_end=date(2026, 8, 31),
                rate_date=date(2026, 8, 31),
                monetary_items=[{"account_code": "1122"}],  # missing currency_code
                actor=FIXED_ACTOR,
            )

    def test_approve_persists(self):
        reval_repo = MagicMock()
        run = RevaluationRun(
            id=uuid4(),
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
        )
        reval_repo.get_run.return_value = run
        svc = self._service(reval_repo)
        svc.approve_run(run.id, approver=uuid4())
        assert run.status == RevaluationStatus.APPROVED
        reval_repo.save_run.assert_called_with(run)

    def test_approve_missing_run(self):
        reval_repo = MagicMock()
        reval_repo.get_run.return_value = None
        svc = self._service(reval_repo)
        with pytest.raises(RevaluationError):
            svc.approve_run(uuid4(), approver=FIXED_ACTOR)

    def test_approve_self_approval_blocked(self):
        """D9 SOD: run creator (actor) must not approve own run."""
        reval_repo = MagicMock()
        run = RevaluationRun(
            id=uuid4(),
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
        )
        reval_repo.get_run.return_value = run
        svc = self._service(reval_repo)
        with pytest.raises(RevaluationError):
            svc.approve_run(run.id, approver=FIXED_ACTOR)
        reval_repo.save_run.assert_not_called()

    def test_post_requires_balanced_entries(self):
        reval_repo = MagicMock()
        run = RevaluationRun(
            id=uuid4(),
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
            entries=[
                RevaluationEntry(
                    account_code="1122",
                    currency_code="USD",
                    balance_original=Decimal("1000"),
                    rate_applied=Decimal("24700"),
                    old_vnd=Decimal("24000000"),
                    new_vnd=Decimal("24700000"),
                    difference=Decimal("700000"),
                    posting_side=PostingSide.DEBIT,
                )
            ],
            status=RevaluationStatus.APPROVED,
        )
        reval_repo.get_run.return_value = run
        svc = self._service(reval_repo)
        with pytest.raises(RevaluationError):
            svc.post_run(run.id)
        reval_repo.save_run.assert_not_called()
