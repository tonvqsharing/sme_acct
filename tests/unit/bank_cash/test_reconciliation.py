"""Unit tests for BankReconciliation (fake repos + fake balance provider)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.bank_cash.services import (
    AlreadyResolvedError,
    NotBalancedError,
    NotFoundError,
    ReconciliationService,
    SodViolationError,
)

COMPANY = uuid4()
BANK = uuid4()
PREPARER = uuid4()
APPROVER = uuid4()


class FakeRecRepo:
    def __init__(self):
        self.rows = {}

    def create(self, r):
        self.rows[r.id] = r
        return r

    def get_by_id(self, rid):
        return self.rows.get(rid)

    def update(self, r):
        self.rows[r.id] = r
        return r

    def get_by_company(self, cid):
        return [x for x in self.rows.values() if x.company_id == cid]


def _svc(internal=Decimal(1000000)):
    provider = lambda cid, bid, as_of: internal
    return ReconciliationService(FakeRecRepo(), internal_provider=provider)


def _create(svc, statement=Decimal(1000000)):
    return svc.create_reconciliation(
        company_id=COMPANY,
        bank_account_id=BANK,
        reconciliation_date=date(2026, 8, 31),
        statement_balance=statement,
        actor=PREPARER,
        reason="month end",
    )


class TestCreate:
    def test_difference_computed_statement_minus_internal(self):
        rec = _create(_svc(internal=Decimal(990000)), statement=Decimal(1000000))
        assert rec.internal_balance == Decimal(990000)
        assert rec.difference == Decimal(10000)
        assert rec.is_resolved is False
        assert len(rec.checksum) == 64

    def test_balanced_when_within_tolerance(self):
        rec = _create(_svc(internal=Decimal("999999.995")), statement=Decimal(1000000))
        assert abs(rec.difference) <= Decimal("0.01")


class TestResolve:
    def test_second_actor_resolves_balanced(self):
        svc = _svc()  # internal == statement → diff 0
        rec = _create(svc)
        out = svc.resolve_reconciliation(rec.id, APPROVER, "verified vs sổ phụ")
        assert out.is_resolved is True
        assert out.resolved_at is not None

    def test_creator_cannot_resolve_sod(self):
        svc = _svc()
        rec = _create(svc)
        with pytest.raises(SodViolationError):
            svc.resolve_reconciliation(rec.id, PREPARER, "self")

    def test_unbalanced_cannot_resolve(self):
        svc = _svc(internal=Decimal(1))  # huge gap
        rec = _create(svc, statement=Decimal(1000000))
        with pytest.raises(NotBalancedError):
            svc.resolve_reconciliation(rec.id, APPROVER, "still off")

    def test_double_resolve_blocked(self):
        svc = _svc()
        rec = _create(svc)
        svc.resolve_reconciliation(rec.id, APPROVER, "ok")
        with pytest.raises(AlreadyResolvedError):
            svc.resolve_reconciliation(rec.id, uuid4(), "again")

    def test_unknown_raises(self):
        with pytest.raises(NotFoundError):
            _svc().resolve_reconciliation(uuid4(), APPROVER, "ghost")


class TestQueries:
    def test_list_filters_resolved(self):
        svc = _svc()
        open_rec = _create(svc)
        done = svc.create_reconciliation(
            company_id=COMPANY,
            bank_account_id=BANK,
            reconciliation_date=date(2026, 7, 31),
            statement_balance=Decimal(1000000),
            actor=PREPARER,
            reason="july",
        )
        svc.resolve_reconciliation(done.id, APPROVER, "ok")
        unresolved = svc.list_by_company(COMPANY, resolved=False)
        assert [r.id for r in unresolved] == [open_rec.id]
