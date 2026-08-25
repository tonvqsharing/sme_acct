"""Unit tests — RevaluationRun engine (specs-currencies §4)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.currencies.domain import (
    RateType,
    RevaluationStatus,
)
from src.bricks.currencies.services import (
    EmptyRunError,
    PeriodLockedError,
    RevaluationService,
    SodViolationError,
    UnknownRateError,
)

COMPANY = uuid4()
PREPARER = uuid4()
APPROVER = uuid4()


def _items():
    """Two FX monetary items at period end."""
    return [
        {
            "account_code": "1122",
            "currency_code": "USD",
            "balance_original": "1000",
            "old_vnd": "25000000",
        },
        {
            "account_code": "1311",
            "currency_code": "EUR",
            "balance_original": "500",
            "old_vnd": "13000000",
        },
    ]


class FakeRates:
    def latest(self, code, rate_type, on_date):
        rates = {"USD": Decimal(26000), "EUR": Decimal(26500)}
        if code not in rates:
            raise UnknownRateError(code)
        assert rate_type == RateType.TRANSFER
        return type("R", (), {"rate": rates[code]})


class FakeRepo:
    def __init__(self):
        self.rows = []

    def create(self, run):
        self.rows.append(run)
        return run

    def update(self, run):
        for i, r in enumerate(self.rows):
            if r.id == run.id:
                self.rows[i] = run
        return run

    def get_by_id(self, rid):
        return next((r for r in self.rows if r.id == rid), None)

    def find_posted_overlap(self, cid, start, end):
        return next(
            (r for r in self.rows if r.company_id == cid and r.status == RevaluationStatus.POSTED),
            None,
        )


@pytest.fixture()
def svc():
    def locked(cid):
        return False

    return RevaluationService(
        rates=FakeRates(),
        repo=FakeRepo(),
        monetary_items=lambda cid: _items(),
        period_locked=locked,
    )


class TestComputeDraft:
    def test_draft_entries_use_transfer_closing_rate(self, svc):
        run = svc.create_run(
            COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=PREPARER,
        )
        assert run.status == RevaluationStatus.DRAFT
        usd = next(e for e in run.entries if e.currency_code == "USD")
        assert usd.new_vnd == Decimal(26000000)  # 1000 × 26,000
        assert usd.difference == Decimal(1000000)  # gain vs 25M
        eur = next(e for e in run.entries if e.currency_code == "EUR")
        assert eur.new_vnd == Decimal(13250000)  # 500 × 26,500
        assert eur.difference == Decimal(250000)

    def test_posting_side_gain_loss(self, svc):
        run = svc.create_run(
            COMPANY,
            date(2026, 8, 1),
            date(2026, 8, 31),
            date(2026, 8, 31),
            actor=PREPARER,
        )
        assert all(e.posting_side == "GAIN" for e in run.entries)

    def test_loss_side_when_vnd_falls(self, svc):
        class WeakUSD(FakeRates):
            def latest(self, code, rt, d):
                r = super().latest(code, rt, d)
                r.rate = Decimal(24000) if code == "USD" else r.rate
                return r

        svc2 = RevaluationService(
            rates=WeakUSD(),
            repo=FakeRepo(),
            monetary_items=lambda cid: _items(),
            period_locked=lambda c: False,
        )
        run = svc2.create_run(
            COMPANY,
            date(2026, 8, 1),
            date(2026, 8, 31),
            date(2026, 8, 31),
            actor=PREPARER,
        )
        usd = next(e for e in run.entries if e.currency_code == "USD")
        assert usd.posting_side == "LOSS"
        assert usd.difference == Decimal(-1000000)

    def test_period_locked_guard(self):
        svc = RevaluationService(
            rates=FakeRates(),
            repo=FakeRepo(),
            monetary_items=lambda cid: _items(),
            period_locked=lambda c: True,
        )
        with pytest.raises(PeriodLockedError):
            svc.create_run(
                COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
            )

    def test_unknown_currency_raises(self):
        jpy_items = [
            {
                "account_code": "1122",
                "currency_code": "JPY",
                "balance_original": "1000",
                "old_vnd": "100",
            }
        ]
        svc = RevaluationService(
            rates=FakeRates(),
            repo=FakeRepo(),
            monetary_items=lambda cid: jpy_items,
            period_locked=lambda c: False,
        )
        with pytest.raises(UnknownRateError):
            svc.create_run(
                COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
            )


class TestApprovalFlow:
    def _draft(self, svc):
        return svc.create_run(
            COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
        )

    def test_submit_then_approve_sod(self, svc):
        run = self._draft(svc)
        pend = svc.submit_for_approval(run.id, PREPARER)
        assert pend.status == RevaluationStatus.PENDING_APPROVAL
        with pytest.raises(SodViolationError):
            svc.approve(pend.id, PREPARER)
        ok = svc.approve(pend.id, APPROVER)
        assert ok.status == RevaluationStatus.APPROVED

    def test_post_approved_marks_posted_with_checksum(self, svc):
        run = self._draft(svc)
        svc.submit_for_approval(run.id, PREPARER)
        svc.approve(run.id, APPROVER)
        posted = svc.post(run.id, uuid4())
        assert posted.status == RevaluationStatus.POSTED
        assert len(posted.checksum) == 64

    def test_empty_items_rejected(self):
        empty = RevaluationService(
            rates=FakeRates(),
            repo=FakeRepo(),
            monetary_items=lambda c: [],
            period_locked=lambda c: False,
        )
        with pytest.raises(EmptyRunError):
            empty.create_run(
                COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
            )


class TestIdempotentRerun:
    def test_rerun_reverses_prior_posted(self, svc):
        r1 = svc.create_run(
            COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
        )
        svc.submit_for_approval(r1.id, PREPARER)
        svc.approve(r1.id, APPROVER)
        svc.post(r1.id, uuid4())

        r2 = svc.create_run(
            COMPANY, date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31), actor=PREPARER
        )
        assert r1.status == RevaluationStatus.REVERSED
        # reversal flips each entry's difference sign
        old_usd = next(e for e in r1.entries if e.currency_code == "USD")
        rev = next(e for e in r2.reversal_entries if e.currency_code == old_usd.currency_code)
        assert rev.difference == -old_usd.difference
