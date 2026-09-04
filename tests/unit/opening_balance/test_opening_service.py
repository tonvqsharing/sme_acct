"""TDD RED — Opening S1: batch + GL + bank + lock + voucher gate."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.opening_balance.domain import BatchSource, BatchState
from src.bricks.opening_balance.services import (
    BatchLockedError,
    OpeningService,
    UnbalancedOpeningError,
)

COMPANY = uuid4()
FY_ID = uuid4()


class FakeFY:
    def get_by_id(self, fy_id):
        if fy_id == FY_ID:
            return type("FY", (), {"company_id": COMPANY})
        return None

    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        if code == "9999":
            raise ValueError("unknown")


class FakeRepo:
    def __init__(self):
        self.batches: dict = {}
        self.gl: dict = {}
        self.bank: dict = {}

    def create_batch(self, b):
        self.batches[b.id] = b
        return b

    def get_batch(self, bid):
        return self.batches.get(bid)

    def update_batch(self, b):
        self.batches[b.id] = b
        return b

    def list_batches(self, cid):
        return [b for b in self.batches.values() if b.company_id == cid]

    def add_gl(self, row):
        self.gl.setdefault(row.batch_id, []).append(row)
        return row

    def list_gl(self, bid):
        return list(self.gl.get(bid, []))

    def add_bank(self, row):
        self.bank.setdefault(row.batch_id, []).append(row)
        return row

    def list_bank(self, bid):
        return list(self.bank.get(bid, []))

    def list_counterparty(self, bid):
        return []


def _svc(**kw):
    return OpeningService(repo=FakeRepo(), fy_years=FakeFY(), coa=FakeCOA(), audit=None, **kw)


def test_create_draft_batch():
    svc = _svc()
    b = svc.create_batch(
        company_id=COMPANY,
        fiscal_year_id=FY_ID,
        source="MANUAL",
        actor=uuid4(),
        reason="init",
    )
    assert b.state == BatchState.DRAFT
    assert b.source == BatchSource.MANUAL


def test_post_gl_and_reconcile_balanced():
    svc = _svc()
    b = svc.create_batch(
        company_id=COMPANY, fiscal_year_id=FY_ID, source="MANUAL", actor=uuid4(), reason="b"
    )
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1111", "debit": "500", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "500"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    rep = svc.reconcile(b.id)
    assert rep["balanced"] is True


def test_lock_unbalanced_409():
    svc = _svc()
    b = svc.create_batch(
        company_id=COMPANY, fiscal_year_id=FY_ID, source="MANUAL", actor=uuid4(), reason="b"
    )
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1111", "debit": "500", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "400"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    with pytest.raises(UnbalancedOpeningError):
        svc.lock(b.id, actor=uuid4(), reason="go-live")


def test_locked_batch_rejects_posts_and_reopen_needs_chief():
    svc = _svc()
    b = svc.create_batch(
        company_id=COMPANY, fiscal_year_id=FY_ID, source="MANUAL", actor=uuid4(), reason="b"
    )
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1111", "debit": "500", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "500"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    svc.lock(b.id, actor=uuid4(), reason="go-live")
    with pytest.raises(BatchLockedError):
        svc.post_gl(b.id, lines=[], actor=uuid4(), reason="late")
    with pytest.raises(PermissionError):
        svc.reopen(b.id, actor=uuid4(), reason="fix", is_chief=False)
    reopened = svc.reopen(b.id, actor=uuid4(), reason="fix", is_chief=True)
    assert reopened.state == BatchState.DRAFT


def test_bank_opening_round_trip():
    svc = _svc()
    b = svc.create_batch(
        company_id=COMPANY, fiscal_year_id=FY_ID, source="MANUAL", actor=uuid4(), reason="b"
    )
    svc.post_bank(
        b.id,
        rows=[{"bank_account_id": str(uuid4()), "amount": "750"}],
        actor=uuid4(),
        reason="bank",
    )
    rep = svc.reconcile(b.id)
    assert rep["checks"]["bank_total"] == Decimal(750)


def test_is_locked_gate_semantics():
    svc = _svc()
    assert svc.is_locked(COMPANY) is None  # no batches → gate skipped
    b = svc.create_batch(
        company_id=COMPANY, fiscal_year_id=FY_ID, source="MANUAL", actor=uuid4(), reason="b"
    )
    assert svc.is_locked(COMPANY) is False
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1111", "debit": "500", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "500"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    svc.lock(b.id, actor=uuid4(), reason="go-live")
    assert svc.is_locked(COMPANY) is True


def test_voucher_gate_raises_without_lock():
    from src.bricks.voucher.services import NoOpeningLockError, VoucherService

    class FakeNumbering:
        def issue(self, cid):
            return "PT/000001"

    vsvc = VoucherService(
        fy=FakeFY(),
        coa=FakeCOA(),
        numbering=FakeNumbering(),
        audit=None,
        opening_locked=lambda cid: False,
    )
    with pytest.raises(NoOpeningLockError):
        vsvc.create_voucher(
            company_id=COMPANY,
            entry_date=date(2026, 8, 10),
            description="live",
            lines=[
                {"account_code": "1111", "debit": "100", "credit": "0"},
                {"account_code": "4111", "debit": "0", "credit": "100"},
            ],
            actor=uuid4(),
            reason="live",
        )
