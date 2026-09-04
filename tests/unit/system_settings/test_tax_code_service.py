"""TDD — TaxCode slice 3."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.system_settings.domain import TaxCode
from src.bricks.system_settings.services import TaxCodeService

COMPANY = uuid4()


class FakeRepo:
    def __init__(self):
        self.codes: dict = {}

    def get_by_code(self, cid, code):
        for c in self.codes.values():
            if c.company_id == cid and c.code == code:
                return c
        return None

    def create_tax_code(self, tc):
        self.codes[tc.id] = tc
        return tc

    def list_tax_codes(self, cid):
        return [c for c in self.codes.values() if c.company_id == cid]


def _svc():
    return TaxCodeService(repo=FakeRepo(), audit=None)


def test_create_tax_code():
    svc = _svc()
    tc = svc.create_tax_code(
        company_id=COMPANY,
        code="VAT-10",
        rate=10,
        type="output",
        account_code="3331",
        actor=uuid4(),
        reason="init",
    )
    assert tc.rate == 10


def test_duplicate_code_rejected():
    svc = _svc()
    svc.create_tax_code(
        company_id=COMPANY,
        code="VAT-10",
        rate=10,
        type="output",
        account_code="3331",
        actor=uuid4(),
        reason="a",
    )
    with pytest.raises(ValueError, match="đã tồn tại"):
        svc.create_tax_code(
            company_id=COMPANY,
            code="VAT-10",
            rate=10,
            type="output",
            account_code="3331",
            actor=uuid4(),
            reason="b",
        )


def test_invalid_rate_rejected():
    with pytest.raises(ValueError, match="rate"):
        TaxCode(company_id=COMPANY, code="BAD", rate=7, type="output", account_code="3331")
