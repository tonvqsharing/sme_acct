"""TDD — Party Slice 1: MST, duplicate, role, isolation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.party.domain import Party
from src.bricks.party.services import DuplicateCodeError, DuplicateMstError, PartyService

COMPANY = uuid4()
OTHER = uuid4()


class FakeRepo:
    def __init__(self):
        self.parties: dict = {}

    def get_by_code(self, cid, code):
        for p in self.parties.values():
            if p.company_id == cid and p.code == code:
                return p
        return None

    def get_by_mst(self, cid, mst):
        for p in self.parties.values():
            if p.company_id == cid and p.mst == mst:
                return p
        return None

    def create_party(self, p):
        self.parties[p.id] = p
        return p

    def get_party(self, pid):
        return self.parties.get(pid)

    def list_parties(self, cid, role=None):
        lst = [p for p in self.parties.values() if p.company_id == cid]
        if role == "customer":
            lst = [p for p in lst if p.is_customer]
        elif role == "supplier":
            lst = [p for p in lst if p.is_supplier]
        return lst

    def create_department(self, d):
        return d

    def get_department(self, did):
        return None

    def list_departments(self, cid):
        return []


def _svc():
    return PartyService(repo=FakeRepo(), audit=None)


def test_create_customer_with_valid_mst():
    svc = _svc()
    p = svc.create_party(
        company_id=COMPANY,
        code="KH-001",
        name="Cty A",
        mst="0101234567",
        is_customer=True,
        actor=uuid4(),
        reason="init",
    )
    assert p.mst == "0101234567"
    assert p.is_customer


def test_mst_invalid_rejected():
    svc = _svc()
    with pytest.raises(ValueError, match="MST"):
        svc.create_party(
            company_id=COMPANY,
            code="KH-002",
            name="B",
            mst="0000000000",
            is_customer=True,
            actor=uuid4(),
            reason="x",
        )


def test_duplicate_code_409():
    svc = _svc()
    svc.create_party(
        company_id=COMPANY, code="KH-001", name="A", is_customer=True, actor=uuid4(), reason="a"
    )
    with pytest.raises(DuplicateCodeError):
        svc.create_party(
            company_id=COMPANY,
            code="KH-001",
            name="A2",
            is_customer=True,
            actor=uuid4(),
            reason="a2",
        )


def test_duplicate_mst_409():
    svc = _svc()
    svc.create_party(
        company_id=COMPANY,
        code="KH-001",
        name="A",
        mst="0101234567",
        is_customer=True,
        actor=uuid4(),
        reason="a",
    )
    with pytest.raises(DuplicateMstError):
        svc.create_party(
            company_id=COMPANY,
            code="KH-002",
            name="B",
            mst="0101234567",
            is_customer=True,
            actor=uuid4(),
            reason="b",
        )


def test_company_isolation():
    svc = _svc()
    svc.create_party(
        company_id=COMPANY,
        code="KH-001",
        name="A",
        mst="0101234567",
        is_customer=True,
        actor=uuid4(),
        reason="a",
    )
    # same code in OTHER company should be allowed
    p = svc.create_party(
        company_id=OTHER,
        code="KH-001",
        name="A2",
        mst="0101234567",
        is_customer=True,
        actor=uuid4(),
        reason="b",
    )
    assert p.company_id == OTHER


def test_role_filter():
    repo = FakeRepo()
    svc = PartyService(repo=repo, audit=None)
    svc.create_party(
        company_id=COMPANY, code="KH-001", name="A", is_customer=True, actor=uuid4(), reason="a"
    )
    svc.create_party(
        company_id=COMPANY, code="NCC-001", name="B", is_supplier=True, actor=uuid4(), reason="b"
    )
    assert len(svc.list_parties(COMPANY, "customer")) == 1
    assert len(svc.list_parties(COMPANY, "supplier")) == 1


def test_at_least_one_role_required():
    with pytest.raises(ValueError, match="at least one role"):
        Party(company_id=COMPANY, code="X", name="Y")
