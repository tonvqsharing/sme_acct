"""Invoice brick unit tests — fakes for FY/COA/numbering/terms ports."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.invoice.services import (
    AggregateAccountError,
    InactiveAccountError,
    InvoiceService,
    NoOpenPeriodError,
    PeriodClosedError,
    UnknownAccountError,
)

COMPANY = uuid4()
TERM_ID = uuid4()


class FakeFY:
    def __init__(self, open_on=True):
        self.open_on = open_on

    def find_open_period(self, company_id, on_date):
        if self.open_on and company_id == COMPANY:
            return type("P", (), {"sequence": 8})
        return None


class ClosedFY(FakeFY):
    """Date falls in a year but its period is CLOSED."""

    def __init__(self):
        super().__init__(open_on=False)

    def find_any_period(self, company_id, on_date):  # not used by service yet
        return None


class FakeCOA:
    def validate_posting_account(self, company_id, code, regime="tt133"):
        if code == "9999":
            raise UnknownAccountError(code)
        if code == "1120":
            raise AggregateAccountError(code)
        if code == "1129":
            raise InactiveAccountError(code)


class FakeNumbering:
    def next_number(self, company_id):
        return f"HD/{self.seq:06d}"

    def __init__(self):
        self.seq = 1

    def issue(self, company_id):
        n = f"HD/{self.seq:06d}"
        self.seq += 1
        return n


class FakeTerms:
    def get_default(self, company_id):
        t = type("T", (), {})
        t.id = TERM_ID
        t.due_days = 30
        return t


ITEMS = [
    {"account_code": "5111", "description": "Doanh thu bán hàng", "amount": "10000000"},
    {"account_code": "1311", "description": "Phải thu KH A", "amount": "11000000"},
]


@pytest.fixture()
def svc():
    return InvoiceService(
        fy=FakeFY(),
        coa=FakeCOA(),
        numbering=FakeNumbering(),
        terms=FakeTerms(),
        audit=None,
    )


def _body():
    return {
        "company_id": COMPANY,
        "customer_name": "Công ty ABC",
        "issue_date": date(2026, 8, 10),
        "vat_rate": Decimal("0.1"),
        "payment_term_id": TERM_ID,
        "items": [dict(i) for i in ITEMS],
    }


class TestCreateInvoice:
    def test_happy_path_numbers_totals_due_date(self, svc):
        inv = svc.create_invoice(actor=uuid4(), reason="sale", **_body())
        assert inv.number == "HD/000001"
        assert inv.subtotal == Decimal(21000000)
        assert inv.vat_amount == Decimal(2100000)
        assert inv.grand_total == Decimal(23100000)
        assert inv.due_date == date(2026, 9, 9)
        assert inv.status.value == "DRAFT"

    def test_second_invoice_gets_next_sequence(self, svc):
        svc.create_invoice(actor=uuid4(), reason="a", **_body())
        second = svc.create_invoice(actor=uuid4(), reason="b", **_body())
        assert second.number == "HD/000002"

    def test_no_open_period_blocked(self):
        svc = InvoiceService(
            fy=FakeFY(open_on=False),
            coa=FakeCOA(),
            numbering=FakeNumbering(),
            terms=FakeTerms(),
            audit=None,
        )
        with pytest.raises((NoOpenPeriodError, PeriodClosedError)):
            svc.create_invoice(actor=uuid4(), reason="r", **_body())

    @pytest.mark.parametrize(
        "bad_code,exc",
        [
            ("9999", UnknownAccountError),
            ("1120", AggregateAccountError),
            ("1129", InactiveAccountError),
        ],
    )
    def test_coa_gate_blocks_bad_accounts(self, bad_code, exc):
        body = _body()
        body["items"] = [dict(ITEMS[0], account_code=bad_code)]
        svc = InvoiceService(
            fy=FakeFY(), coa=FakeCOA(), numbering=FakeNumbering(), terms=FakeTerms(), audit=None
        )
        with pytest.raises(exc):
            svc.create_invoice(actor=uuid4(), reason="r", **body)

    def test_empty_items_rejected(self, svc):
        body = _body()
        body["items"] = []
        with pytest.raises(ValueError, match="items"):
            svc.create_invoice(actor=uuid4(), reason="r", **body)


class TestPost:
    def test_post_flips_status_and_audits(self, svc):
        from src.bricks.invoice.domain import GENESIS_CHECKSUM  # noqa: F401

        inv = svc.create_invoice(actor=uuid4(), reason="a", **_body())
        posted = svc.post_invoice(inv.id, actor=uuid4(), reason="ok")
        assert posted.status.value == "POSTED"
        assert len(posted.checksum) == 64

    def test_double_post_blocked(self, svc):
        from src.bricks.invoice.services import AlreadyPostedError

        inv = svc.create_invoice(actor=uuid4(), reason="a", **_body())
        svc.post_invoice(inv.id, actor=uuid4(), reason="first")
        with pytest.raises(AlreadyPostedError):
            svc.post_invoice(inv.id, actor=uuid4(), reason="again")

    def test_post_unknown_raises(self, svc):
        from src.bricks.invoice.services import InvoiceNotFoundError

        with pytest.raises(InvoiceNotFoundError):
            svc.post_invoice(uuid4(), actor=uuid4(), reason="x")


class TestVatRates:
    @pytest.mark.parametrize(
        "rate,expect_vat",
        [
            ("0.1", "2100000"),
            ("0.08", "1680000"),
            ("0", "0"),
        ],
    )
    def test_vn_vat_rates(self, rate, expect_vat):
        svc = InvoiceService(
            fy=FakeFY(), coa=FakeCOA(), numbering=FakeNumbering(), terms=FakeTerms(), audit=None
        )
        body = _body()
        body["vat_rate"] = Decimal(rate)
        inv = svc.create_invoice(actor=uuid4(), reason="r", **body)
        assert inv.vat_amount == Decimal(expect_vat)
