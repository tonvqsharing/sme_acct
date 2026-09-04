"""TDD RED — Opening S2: counterparty AR/AP + aging hook."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.ledger.services import LedgerService
from src.bricks.opening_balance.services import BatchLockedError, NotFoundError, OpeningService

COMPANY = uuid4()
FY_ID = uuid4()
PARTY_ID = uuid4()
OTHER_PARTY = uuid4()


class FakeFY:
    def get_by_id(self, fy_id):
        if fy_id == FY_ID:
            return type("FY", (), {"company_id": COMPANY})
        return None

    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        return None


class FakeParty:
    def __init__(self, cid, active=True):
        self.company_id = cid
        self.active = active


class FakeRepo:
    def __init__(self):
        self.batches: dict = {}
        self.gl: dict = {}
        self.cp: dict = {}
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

    def add_counterparty(self, row):
        self.cp.setdefault(row.batch_id, []).append(row)
        return row

    def list_counterparty(self, bid):
        return list(self.cp.get(bid, []))

    def list_stock(self, bid):
        return []


def _parties(pid):
    if pid == PARTY_ID:
        return FakeParty(COMPANY)
    if pid == OTHER_PARTY:
        return FakeParty(uuid4())
    return None


def _svc(**kw):
    return OpeningService(
        repo=FakeRepo(),
        fy_years=FakeFY(),
        coa=FakeCOA(),
        audit=None,
        party_lookup=_parties,
        **kw,
    )


def _batch(svc):
    return svc.create_batch(
        company_id=COMPANY,
        fiscal_year_id=FY_ID,
        source="MANUAL",
        actor=uuid4(),
        reason="b",
    )


def test_post_counterparty_ok():
    svc = _svc()
    b = _batch(svc)
    svc.post_counterparty(
        b.id,
        rows=[
            {"account_code": "1311", "party_id": str(PARTY_ID), "side": "debit", "amount": "200"}
        ],
        actor=uuid4(),
        reason="ar",
    )
    rep = svc.reconcile(b.id)
    assert rep["checks"]["counterparty_total"] == Decimal(200)


def test_unknown_party_404():
    svc = _svc()
    b = _batch(svc)
    with pytest.raises(NotFoundError):
        svc.post_counterparty(
            b.id,
            rows=[
                {"account_code": "1311", "party_id": str(uuid4()), "side": "debit", "amount": "1"}
            ],
            actor=uuid4(),
            reason="x",
        )


def test_cross_company_party_422():
    svc = _svc()
    b = _batch(svc)
    with pytest.raises(ValueError, match="công ty"):
        svc.post_counterparty(
            b.id,
            rows=[
                {
                    "account_code": "1311",
                    "party_id": str(OTHER_PARTY),
                    "side": "debit",
                    "amount": "1",
                }
            ],
            actor=uuid4(),
            reason="x",
        )


def test_locked_batch_rejects_counterparty():
    svc = _svc()
    b = _batch(svc)
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1111", "debit": "100", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "100"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    svc.lock(b.id, actor=uuid4(), reason="go")
    with pytest.raises(BatchLockedError):
        svc.post_counterparty(
            b.id,
            rows=[
                {"account_code": "1311", "party_id": str(PARTY_ID), "side": "debit", "amount": "1"}
            ],
            actor=uuid4(),
            reason="late",
        )


def test_aging_hook_adds_opening_to_current():
    svc = _svc()
    b = _batch(svc)
    svc.post_counterparty(
        b.id,
        rows=[
            {"account_code": "1311", "party_id": str(PARTY_ID), "side": "debit", "amount": "200"}
        ],
        actor=uuid4(),
        reason="ar",
    )
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "1311", "debit": "200", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "200"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    svc.lock(b.id, actor=uuid4(), reason="go")

    class FakeSource:
        def get_posted_lines(self, cid, start, end):
            return []

    ledger = LedgerService(
        source=FakeSource(),
        opening_balances=lambda cid: (
            [{"account_code": "1311", "side": "debit", "amount": Decimal(200)}]
            if cid == COMPANY
            else []
        ),
    )
    buckets = {r["bucket"]: r["amount"] for r in ledger.ar_aging(COMPANY, date(2026, 8, 31))}
    assert buckets["current"] == Decimal(200)
