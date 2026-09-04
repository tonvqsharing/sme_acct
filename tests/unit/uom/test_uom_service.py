"""TDD — UOM slice 2."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.uom.services import DuplicateCodeError, UOMService

COMPANY = uuid4()


class FakeRepo:
    def __init__(self):
        self.uoms: dict = {}

    def get_by_code(self, cid, code):
        for u in self.uoms.values():
            if u.company_id == cid and u.code == code:
                return u
        return None

    def create_uom(self, u):
        self.uoms[u.id] = u
        return u

    def get_uom(self, uid):
        return self.uoms.get(uid)

    def list_uoms(self, cid):
        return [u for u in self.uoms.values() if u.company_id == cid]


def _svc():
    return UOMService(repo=FakeRepo(), audit=None)


def test_create_uom_basic():
    svc = _svc()
    u = svc.create_uom(
        company_id=COMPANY, code="Cai", name="Cái", factor=Decimal(1), actor=uuid4(), reason="init"
    )
    assert u.code == "Cai"


def test_duplicate_code_409():
    svc = _svc()
    svc.create_uom(company_id=COMPANY, code="Cai", name="Cái", actor=uuid4(), reason="a")
    with pytest.raises(DuplicateCodeError):
        svc.create_uom(company_id=COMPANY, code="Cai", name="Cái 2", actor=uuid4(), reason="b")


def test_factor_must_be_positive():
    svc = _svc()
    with pytest.raises(ValueError, match="factor"):
        svc.create_uom(
            company_id=COMPANY, code="Hop", name="Hộp", factor=Decimal(0), actor=uuid4(), reason="x"
        )


def test_uom_with_base():
    svc = _svc()
    base = svc.create_uom(
        company_id=COMPANY, code="Cai", name="Cái", factor=Decimal(1), actor=uuid4(), reason="base"
    )
    hop = svc.create_uom(
        company_id=COMPANY,
        code="Hop",
        name="Hộp 10 cái",
        factor=Decimal(10),
        base_uom_id=base.id,
        actor=uuid4(),
        reason="hop",
    )
    assert hop.base_uom_id == base.id
    assert hop.factor == Decimal(10)
