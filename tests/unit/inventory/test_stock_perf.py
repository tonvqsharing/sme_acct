"""TDD RED — Slice6: moves composite index + stock pagination."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.bricks.inventory.services import InventoryService
from src.bricks.inventory.storage import StockMoveModel

COMPANY = uuid4()


def test_moves_composite_index_exists():
    names = {ix.name for ix in StockMoveModel.__table__.indexes}
    assert "ix_moves_company_product_state" in names


class FakeFY:
    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeNumbering:
    def issue(self, cid, ship_type=None):
        return "PN/000001"


class FakeProduct:
    def __init__(self, cid, code):
        from src.bricks.inventory.domain import CostMethod

        self.id = uuid4()
        self.company_id = cid
        self.code = code
        self.name = code
        self.uom = "Cái"
        self.cost_method = CostMethod.WAVG


class FakeRepo:
    def __init__(self, n_products=3):
        self._prods = [FakeProduct(COMPANY, f"SKU-{i}") for i in range(n_products)]

    def list_products(self, cid):
        return [p for p in self._prods if p.company_id == cid]

    def get_product(self, pid):
        for p in self._prods:
            if p.id == pid:
                return p
        return None

    def get_stock_qty(self, cid, pid, lid=None):
        return Decimal(10)

    def get_stock_value(self, cid, pid):
        return Decimal(100000)


def _svc(n=3):
    return InventoryService(repo=FakeRepo(n), fy=FakeFY(), numbering=FakeNumbering(), audit=None)


def test_get_stock_paginates():
    svc = _svc(3)
    page1 = svc.get_stock(COMPANY, page=1, page_size=2)
    page2 = svc.get_stock(COMPANY, page=2, page_size=2)
    assert len(page1) == 2
    assert len(page2) == 1
    assert page1[0]["code"] != page2[0]["code"]


def test_get_stock_defaults_return_all():
    svc = _svc(3)
    rows = svc.get_stock(COMPANY)
    assert len(rows) == 3
