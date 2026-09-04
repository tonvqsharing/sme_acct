"""TDD RED — Opening S5c: year-roll copies LOCKED rows into new FY batch."""

from __future__ import annotations

from uuid import uuid4

from src.bricks.opening_balance.domain import BatchState
from src.bricks.opening_balance.services import BatchLockedError, OpeningService

COMPANY = uuid4()
FY_OLD = uuid4()
FY_NEW = uuid4()


class FakeFY:
    def get_by_id(self, fy_id):
        if fy_id in (FY_OLD, FY_NEW):
            return type("FY", (), {"company_id": COMPANY})
        return None

    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        return None


class FakeRepo:
    def __init__(self):
        self.batches: dict = {}
        self.gl: dict = {}

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

    def list_bank(self, bid):
        return []

    def list_counterparty(self, bid):
        return []

    def list_stock(self, bid):
        return []

    def list_assets(self, bid):
        return []


def _svc():
    return OpeningService(
        repo=FakeRepo(),
        fy_years=FakeFY(),
        coa=FakeCOA(),
        audit=None,
    )


def test_rollover_copies_locked_gl_into_new_draft():
    svc = _svc()
    src = svc.create_batch(
        company_id=COMPANY,
        fiscal_year_id=FY_OLD,
        source="MANUAL",
        actor=uuid4(),
        reason="b",
    )
    svc.post_gl(
        src.id,
        lines=[
            {"account_code": "1111", "debit": "500", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "500"},
        ],
        actor=uuid4(),
        reason="gl",
    )
    svc.lock(src.id, actor=uuid4(), reason="go")

    rolled = svc.rollover(src.id, new_fiscal_year_id=FY_NEW, actor=uuid4(), reason="y2027")
    assert rolled.state == BatchState.DRAFT
    assert rolled.fiscal_year_id == FY_NEW
    lines = svc._repo.list_gl(rolled.id)
    assert sorted((str(l.debit), str(l.credit)) for l in lines) == [("0", "500"), ("500", "0")]


def test_rollover_requires_locked_source():
    svc = _svc()
    src = svc.create_batch(
        company_id=COMPANY,
        fiscal_year_id=FY_OLD,
        source="MANUAL",
        actor=uuid4(),
        reason="b",
    )
    try:
        svc.rollover(src.id, new_fiscal_year_id=FY_NEW, actor=uuid4(), reason="y2027")
    except BatchLockedError:
        return
    raise AssertionError("expected BatchLockedError for DRAFT source")
