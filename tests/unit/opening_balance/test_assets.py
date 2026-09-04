"""TDD RED — Opening S4a: FA opening + bank/FA ties."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.opening_balance.services import OpeningService, UnbalancedOpeningError

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
        return None


class FakeFA:
    def __init__(self):
        self.created: list = []

    def create_asset(self, **kw):
        self.created.append(kw)
        return kw


class FakeRepo:
    def __init__(self):
        self.batches: dict = {}
        self.gl: dict = {}
        self.bank: dict = {}
        self.cp: dict = {}
        self.stock: dict = {}
        self.assets: dict = {}

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
        return list(self.cp.get(bid, []))

    def list_stock(self, bid):
        return list(self.stock.get(bid, []))

    def add_asset(self, row):
        self.assets.setdefault(row.batch_id, []).append(row)
        return row

    def list_assets(self, bid):
        return list(self.assets.get(bid, []))


def _svc(**kw):
    return OpeningService(
        repo=FakeRepo(),
        fy_years=FakeFY(),
        coa=FakeCOA(),
        audit=None,
        fixed_assets=FakeFA(),
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


def _gl(svc, bid, lines):
    svc.post_gl(bid, lines=lines, actor=uuid4(), reason="gl")


def _asset_row(**over):
    base = {
        "kind": "fixed_asset",
        "code": "TSCD-01",
        "name": "Máy CNC",
        "original_cost": "1200000000",
        "remaining_value": "800000000",
        "months_left": 80,
        "expense_account": "6421",
    }
    base.update(over)
    return base


def test_post_asset_materializes_fa_with_accumulated():
    svc = _svc()
    b = _batch(svc)
    svc.post_assets(b.id, rows=[_asset_row()], actor=uuid4(), reason="fa")
    fa = svc._fixed_assets.created[0]
    assert fa["asset_code"] == "TSCD-01"
    assert fa["accumulated_depreciation"] == Decimal(400000000)
    assert fa["useful_life_months"] >= 80


def test_asset_remaining_must_not_exceed_original():
    svc = _svc()
    b = _batch(svc)
    with pytest.raises(ValueError, match="remaining"):
        svc.post_assets(
            b.id,
            rows=[_asset_row(remaining_value="2000000000")],
            actor=uuid4(),
            reason="fa",
        )


def test_bank_tie_enforced_at_lock():
    svc = _svc()
    b = _batch(svc)
    _gl(
        svc,
        b.id,
        [
            {"account_code": "1121", "debit": "700", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "700"},
        ],
    )
    svc.post_bank(
        b.id,
        rows=[{"bank_account_id": str(uuid4()), "amount": "500"}],
        actor=uuid4(),
        reason="bank",
    )
    with pytest.raises(UnbalancedOpeningError, match="112"):
        svc.lock(b.id, actor=uuid4(), reason="go")


def test_fa_tie_enforced_at_lock():
    svc = _svc()
    b = _batch(svc)
    svc.post_assets(b.id, rows=[_asset_row()], actor=uuid4(), reason="fa")
    _gl(
        svc,
        b.id,
        [
            {"account_code": "2111", "debit": "1000000000", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "1000000000"},
        ],
    )
    with pytest.raises(UnbalancedOpeningError, match="211"):
        svc.lock(b.id, actor=uuid4(), reason="go")
