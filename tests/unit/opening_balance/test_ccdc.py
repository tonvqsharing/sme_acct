"""TDD RED — Opening S4b: CCDC rows route to ccdc port + 242 tie."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

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


class FakeCCDC:
    def __init__(self):
        self.opened: list = []

    def open_ccdc_with_history(self, **kw):
        self.opened.append(kw)
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
        ccdc=FakeCCDC(),
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


def _ccdc_row(**over):
    base = {
        "kind": "ccdc",
        "code": "CCDC-01",
        "name": "Máy khoan",
        "original_cost": "12000000",
        "remaining_value": "7000000",
        "months_left": 7,
        "expense_account": "627",
    }
    base.update(over)
    return base


def test_post_ccdc_routes_to_ccdc_port():
    svc = _svc()
    b = _batch(svc)
    svc.post_assets(b.id, rows=[_ccdc_row()], actor=uuid4(), reason="ccdc")
    opened = svc._ccdc.opened[0]
    assert opened["code"] == "CCDC-01"
    assert opened["remaining_value"] == Decimal(7000000)
    assert opened["months_left"] == 7
    assert len(svc._repo.list_assets(b.id)) == 1


def test_ccdc_242_tie_enforced_at_lock():
    svc = _svc()
    b = _batch(svc)
    svc.post_assets(b.id, rows=[_ccdc_row()], actor=uuid4(), reason="ccdc")
    svc.post_gl(
        b.id,
        lines=[
            {"account_code": "2421", "debit": "5000000", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "5000000"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    try:
        svc.lock(b.id, actor=uuid4(), reason="go")
    except UnbalancedOpeningError as exc:
        assert "242" in str(exc)
    else:
        raise AssertionError("expected 242 tie failure")
