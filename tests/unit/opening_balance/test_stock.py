"""TDD RED — Opening S3: stock rows + SKU=GL tie."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.opening_balance.services import (
    BatchLockedError,
    OpeningService,
    UnbalancedOpeningError,
)

COMPANY = uuid4()
FY_ID = uuid4()
PROD_ID = uuid4()
LOC_ID = uuid4()
CAT_ID = uuid4()


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


class FakeProduct:
    def __init__(self):
        self.id = PROD_ID
        self.company_id = COMPANY
        self.active = True
        self.category_id = CAT_ID
        self.cost_method = type("CM", (), {"value": "wavg"})()


class FakeCategory:
    def __init__(self):
        self.id = CAT_ID
        self.company_id = COMPANY
        self.account_code = "1521"


class FakeLocation:
    def __init__(self):
        self.id = LOC_ID
        self.company_id = COMPANY


class FakeInventory:
    def __init__(self):
        self.moves: list = []

    def get_product(self, pid):
        return FakeProduct() if pid == PROD_ID else None

    def get_location(self, lid):
        return FakeLocation() if lid == LOC_ID else None

    def get_category(self, cid):
        return FakeCategory() if cid == CAT_ID else None

    def post_opening_move(self, **kw):
        self.moves.append(kw)
        return kw


class FakeRepo:
    def __init__(self):
        self.batches: dict = {}
        self.gl: dict = {}
        self.bank: dict = {}
        self.cp: dict = {}
        self.stock: dict = {}

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

    def add_stock(self, row):
        self.stock.setdefault(row.batch_id, []).append(row)
        return row

    def list_stock(self, bid):
        return list(self.stock.get(bid, []))


def _svc(**kw):
    return OpeningService(
        repo=FakeRepo(),
        fy_years=FakeFY(),
        coa=FakeCOA(),
        audit=None,
        inventory=FakeInventory(),
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


def _gl(svc, bid, debit="1000"):
    svc.post_gl(
        bid,
        lines=[
            {"account_code": "1521", "debit": debit, "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": debit},
        ],
        actor=uuid4(),
        reason="gl",
    )


def test_post_stock_materializes_move():
    svc = _svc()
    b = _batch(svc)
    svc.post_stock(
        b.id,
        rows=[
            {
                "product_id": str(PROD_ID),
                "warehouse_id": str(LOC_ID),
                "qty": "100",
                "total_value": "1000000",
            }
        ],
        actor=uuid4(),
        reason="stock",
    )
    assert len(svc._inventory.moves) == 1
    mv = svc._inventory.moves[0]
    assert mv["qty"] == Decimal(100)
    assert mv["unit_cost"] == Decimal(10000)


def test_stock_gl_tie_enforced_at_lock():
    svc = _svc()
    b = _batch(svc)
    svc.post_stock(
        b.id,
        rows=[
            {
                "product_id": str(PROD_ID),
                "warehouse_id": str(LOC_ID),
                "qty": "100",
                "total_value": "1000000",
            }
        ],
        actor=uuid4(),
        reason="stock",
    )
    _gl(svc, b.id, debit="900000")  # GL short of SKU total
    with pytest.raises(UnbalancedOpeningError, match="1521"):
        svc.lock(b.id, actor=uuid4(), reason="go")


def test_stock_gl_tie_passes_when_equal():
    svc = _svc()
    b = _batch(svc)
    svc.post_stock(
        b.id,
        rows=[
            {
                "product_id": str(PROD_ID),
                "warehouse_id": str(LOC_ID),
                "qty": "100",
                "total_value": "1000000",
            }
        ],
        actor=uuid4(),
        reason="stock",
    )
    _gl(svc, b.id, debit="1000000")
    locked = svc.lock(b.id, actor=uuid4(), reason="go")
    assert locked.state.value == "LOCKED"


def test_fifo_rows_require_receipt_detail():
    svc = _svc()
    b = _batch(svc)
    with pytest.raises(ValueError, match="receipt"):
        svc.post_stock(
            b.id,
            rows=[
                {
                    "product_id": str(PROD_ID),
                    "warehouse_id": str(LOC_ID),
                    "qty": "10",
                    "total_value": "100000",
                    "cost_method": "fifo",
                }
            ],
            actor=uuid4(),
            reason="stock",
        )


def test_locked_batch_rejects_stock():
    svc = _svc()
    b = _batch(svc)
    svc.post_stock(
        b.id,
        rows=[
            {
                "product_id": str(PROD_ID),
                "warehouse_id": str(LOC_ID),
                "qty": "100",
                "total_value": "1000000",
            }
        ],
        actor=uuid4(),
        reason="stock",
    )
    _gl(svc, b.id, debit="1000000")
    svc.lock(b.id, actor=uuid4(), reason="go")
    with pytest.raises(BatchLockedError):
        svc.post_stock(
            b.id,
            rows=[
                {
                    "product_id": str(PROD_ID),
                    "warehouse_id": str(LOC_ID),
                    "qty": "1",
                    "total_value": "10000",
                }
            ],
            actor=uuid4(),
            reason="late",
        )
