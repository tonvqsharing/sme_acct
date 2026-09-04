"""TDD RED — Opening S5a: gate hardening (any DRAFT blocks; post gated)."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.bricks.opening_balance.domain import BatchSource, BatchState, OpeningBatch
from src.bricks.opening_balance.services import OpeningService

COMPANY = uuid4()
FY_ID = uuid4()


class FakeRepo:
    def __init__(self, batches):
        self._batches = batches

    def list_batches(self, cid):
        return [b for b in self._batches if b.company_id == cid]


def _batch(state):
    return OpeningBatch(
        id=uuid4(),
        company_id=COMPANY,
        fiscal_year_id=FY_ID,
        source=BatchSource.MANUAL,
        state=state,
        checksum="",
    )


def _svc(batches):
    return OpeningService(
        repo=FakeRepo(batches),
        fy_years=None,
        coa=None,
        audit=None,
    )


def test_no_batches_skips_gate():
    assert _svc([]).is_locked(COMPANY) is None


def test_all_locked_passes():
    assert _svc([_batch(BatchState.LOCKED)]).is_locked(COMPANY) is True


def test_any_draft_blocks_even_with_locked():
    svc = _svc([_batch(BatchState.LOCKED), _batch(BatchState.DRAFT)])
    assert svc.is_locked(COMPANY) is False


def test_single_draft_blocks():
    assert _svc([_batch(BatchState.DRAFT)]).is_locked(COMPANY) is False


def test_post_voucher_blocked_without_lock():
    from src.bricks.voucher.services import NoOpeningLockError, VoucherService

    class FakeFY:
        def find_open_period(self, cid, d):
            return type("P", (), {"sequence": 1})

    class FakeCOA:
        def validate_posting_account(self, cid, code, regime="tt133"):
            return None

    class FakeNumbering:
        def issue(self, cid):
            return "PT/000001"

    gate = {"locked": True}
    vsvc = VoucherService(
        fy=FakeFY(),
        coa=FakeCOA(),
        numbering=FakeNumbering(),
        audit=None,
        opening_locked=lambda cid: gate["locked"],
    )
    created = vsvc.create_voucher(
        company_id=COMPANY,
        entry_date=date(2026, 8, 10),
        description="draft before lock",
        lines=[
            {"account_code": "1111", "debit": "100", "credit": "0"},
            {"account_code": "4111", "debit": "0", "credit": "100"},
        ],
        actor=uuid4(),
        reason="draft",
    )
    gate["locked"] = False  # batch reopened after draft created
    with pytest.raises(NoOpeningLockError):
        vsvc.post_voucher(created.id, actor=uuid4(), reason="post")
