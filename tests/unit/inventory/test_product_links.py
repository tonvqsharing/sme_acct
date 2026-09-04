"""TDD RED — Slice4: Product link FK UOM/Category."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.inventory.services import InventoryService

COMPANY = uuid4()
OTHER = uuid4()


class FakeFY:
    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeNumbering:
    def issue(self, cid, ship_type=None):
        return "PN/000001"


class FakeUOM:
    def __init__(self, cid, uid):
        self.company_id = cid
        self.id = uid


class FakeCategory:
    def __init__(self, cid, cid2):
        self.company_id = cid
        self.id = cid2


class FakeRepo:
    def __init__(self, uom_company=COMPANY, cat_company=COMPANY):
        self.products: dict = {}
        self.uom_company = uom_company
        self.cat_company = cat_company
        self.uom_id = uuid4()
        self.cat_id = uuid4()

    def get_product_by_code(self, cid, code):
        return None

    def create_product(self, p):
        self.products[p.id] = p
        return p

    def get_uom(self, uid):
        if uid == self.uom_id:
            return FakeUOM(self.uom_company, uid)
        return None

    def get_category(self, cid):
        if cid == self.cat_id:
            return FakeCategory(self.cat_company, cid)
        return None


def _svc(repo):
    return InventoryService(repo=repo, fy=FakeFY(), numbering=FakeNumbering(), audit=None)


def test_product_links_valid_uom_and_category():
    repo = FakeRepo()
    svc = _svc(repo)
    p = svc.create_product(
        company_id=COMPANY,
        code="SKU-LINK",
        name="Linked",
        uom="Cai",
        cost_method="wavg",
        uom_id=repo.uom_id,
        category_id=repo.cat_id,
        actor=uuid4(),
        reason="link",
    )
    assert p.uom_id == repo.uom_id
    assert p.category_id == repo.cat_id


def test_product_rejects_unknown_uom():
    repo = FakeRepo()
    svc = _svc(repo)
    with pytest.raises(ValueError, match="uom"):
        svc.create_product(
            company_id=COMPANY,
            code="SKU-BAD",
            name="Bad",
            uom="Cai",
            cost_method="wavg",
            uom_id=uuid4(),
            actor=uuid4(),
            reason="bad",
        )


def test_product_rejects_cross_company_category():
    repo = FakeRepo(cat_company=OTHER)
    svc = _svc(repo)
    with pytest.raises(ValueError, match="category"):
        svc.create_product(
            company_id=COMPANY,
            code="SKU-X",
            name="X",
            uom="Cai",
            cost_method="wavg",
            category_id=repo.cat_id,
            actor=uuid4(),
            reason="x",
        )
