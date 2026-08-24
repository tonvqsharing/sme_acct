"""Double-entry voucher unit tests — fakes only."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.voucher.services import (
    AlreadyPostedError,
    InvoiceServiceAdapter,
    NoOpenPeriodError,
    UnbalancedVoucherError,
    VoucherNotFoundError,
    VoucherService,
)

COMPANY = uuid4()


class OpenFY:
    def find_open_period(self, company_id, on_date):
        return object()


class ClosedFY:
    def find_open_period(self, company_id, on_date):
        return None


class OkCOA:
    def __init__(self) -> None:
        self.calls: list = []

    def validate_posting_account(self, company_id, code, regime="tt133"):
        self.calls.append((company_id, code, regime))
        if code == "9999":
            raise ValueError("unknown")


LINES_BALANCED = [
    {"account_code": "1121", "debit": "11000000", "credit": "0"},
    {"account_code": "5111", "debit": "0", "credit": "11000000"},
]
# off by 1 dong → exceeds 0.01 tolerance
LINES_OFF_BY_1 = [
    {"account_code": "1121", "debit": "11000001", "credit": "0"},
    {"account_code": "5111", "debit": "0", "credit": "10000000"},
]


def _body(lines=LINES_BALANCED):
    return {
        "company_id": COMPANY,
        "entry_date": date(2026, 8, 12),
        "description": "Thu tiền khách hàng",
        "lines": [dict(l) for l in lines],
    }


def _svc(fy=None):
    class Num:
        def issue(self, cid):
            return "PT/000001"

    return VoucherService(fy=fy or OpenFY(), coa=OkCOA(), numbering=Num(), audit=None)


class TestCreate:
    def test_balanced_creates_draft(self):
        v = _svc().create_voucher(actor=uuid4(), reason="r", **_body())
        assert v.number == "PT/000001"
        assert v.status.value == "DRAFT"
        assert v.total_debit == Decimal(11000000)
        assert v.total_credit == Decimal(11000000)

    @pytest.mark.parametrize("delta", ["0.02", "1"])
    def test_unbalanced_beyond_tolerance_rejected(self, delta):
        lines = [
            {"account_code": "1121", "debit": str(Decimal(100) + Decimal(delta)), "credit": "0"},
            {"account_code": "5111", "debit": "0", "credit": "100"},
        ]
        with pytest.raises(UnbalancedVoucherError):
            _svc().create_voucher(actor=uuid4(), reason="r", **_body(lines))

    def test_off_by_one_cent_passes(self):
        lines = [
            {"account_code": "1121", "debit": "100.01", "credit": "0"},
            {"account_code": "5111", "debit": "0", "credit": "100"},
        ]
        v = _svc().create_voucher(actor=uuid4(), reason="r", **_body(lines))
        assert v.total_debit == Decimal("100.01")

    def test_closed_period_blocked(self):
        with pytest.raises(NoOpenPeriodError):
            _svc(ClosedFY()).create_voucher(actor=uuid4(), reason="r", **_body())

    def test_unknown_account_propagates(self):
        lines = [{"account_code": "9999", "debit": "1", "credit": "1"}]
        with pytest.raises(ValueError):
            _svc().create_voucher(actor=uuid4(), reason="r", **_body(lines))

    def test_empty_lines_rejected(self):
        with pytest.raises(ValueError, match="lines"):
            _svc().create_voucher(actor=uuid4(), reason="r", **_body([]))

    def test_both_sides_on_one_line_rejected(self):
        lines = [{"account_code": "111", "debit": "5", "credit": "5"}]
        with pytest.raises(ValueError, match="one side"):
            _svc().create_voucher(actor=uuid4(), reason="r", **_body(lines))


class TestPost:
    def test_post_flips_and_checksums(self):
        svc = _svc()
        v = svc.create_voucher(actor=uuid4(), reason="r", **_body())
        posted = svc.post_voucher(v.id, actor=uuid4(), reason="ok")
        assert posted.status.value == "POSTED"
        assert len(posted.checksum) == 64

    def test_double_post_blocked(self):
        svc = _svc()
        v = svc.create_voucher(actor=uuid4(), reason="r", **_body())
        svc.post_voucher(v.id, actor=uuid4(), reason="1st")
        with pytest.raises(AlreadyPostedError):
            svc.post_voucher(v.id, actor=uuid4(), reason="2nd")

    def test_unknown_raises(self):
        with pytest.raises(VoucherNotFoundError):
            _svc().post_voucher(uuid4(), actor=uuid4(), reason="x")


class TestInvoiceAdapter:
    """Invoice → voucher line generation (Nợ 131 / Có 5111)."""

    def test_builds_two_sided_lines_from_invoice(self):
        from src.bricks.invoice.domain import Invoice, InvoiceItem, InvoiceStatus

        inv = Invoice(
            company_id=COMPANY,
            number="HD/000001",
            issue_date=date(2026, 8, 10),
            customer_name="KH",
            items=[
                InvoiceItem("5111", "rev", Decimal(10000000)),
            ],
            vat_rate=Decimal("0.1"),
            due_date=date(2026, 9, 9),
        )
        inv.status = InvoiceStatus.POSTED
        lines = InvoiceServiceAdapter.lines_from_invoice(inv)
        codes = {(l.account_code, l.debit, l.credit) for l in lines}
        assert ("1311", Decimal(11000000), Decimal(0)) in codes
        assert ("5111", Decimal(0), Decimal(10000000)) in codes
