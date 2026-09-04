"""TDD — Sales enhancements S1-S5: line VAT, FX, deductions, TT99, einvoice, checksum."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.invoice.domain import EInvoiceStatus
from src.bricks.invoice.services import InvoiceService

COMPANY = uuid4()
TERM_ID = uuid4()


class FakeFY:
    def __init__(self, open_on=True):
        self.open_on = open_on

    def find_open_period(self, company_id, on_date):
        return type("P", (), {"sequence": 8}) if self.open_on else None


class FakeCOA:
    def validate_posting_account(self, company_id, code, regime="tt133"):
        if code == "9999":
            raise ValueError("unknown")


class FakeNumbering:
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

    def get_payment_term(self, tid):
        return self.get_default(tid)


class FakeVoucher:
    def __init__(self):
        self.last = None

    def create_voucher(self, **kw):
        self.last = kw
        v = type("V", (), {"id": uuid4(), "number": "PT/000001"})()
        return v


def _svc():
    return InvoiceService(
        fy=FakeFY(), coa=FakeCOA(), numbering=FakeNumbering(), terms=FakeTerms(), audit=None
    )


class TestLineLevelVAT:
    def test_mixed_rates_breakdown(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[
                {
                    "account_code": "5111",
                    "amount": "10000000",
                    "vat_rate": "0.05",
                    "description": "sach",
                },
                {
                    "account_code": "5111",
                    "amount": "20000000",
                    "vat_rate": "0.10",
                    "description": "tu van",
                },
                {
                    "account_code": "5111",
                    "amount": "5000000",
                    "vat_rate": "0.08",
                    "category": "manufacturing",
                    "description": "sx",
                },
            ],
            actor=uuid4(),
            reason="mix",
        )
        assert inv.vat_breakdown["0.05"] == Decimal(500000)
        assert inv.vat_breakdown["0.10"] == Decimal(2000000)
        assert inv.vat_breakdown["0.08"] == Decimal(400000)
        assert inv.vat_amount == Decimal(2900000)
        assert inv.grand_total == Decimal(37900000)

    def test_header_fallback_legacy(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[{"account_code": "5111", "amount": "1000000", "description": "a"}],
            actor=uuid4(),
            reason="legacy",
        )
        assert inv.vat_amount == Decimal(100000)

    def test_8pct_panel_override_allows_excluded_category(self):
        svc = InvoiceService(
            fy=FakeFY(),
            coa=FakeCOA(),
            numbering=FakeNumbering(),
            terms=FakeTerms(),
            audit=None,
            exclusion_of=lambda cid, cat=None: True,
        )
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[
                {
                    "account_code": "5111",
                    "amount": "1000",
                    "vat_rate": "0.08",
                    "category": "telecom",
                }
            ],
            actor=uuid4(),
            reason="panel override",
        )
        assert inv.vat_breakdown["0.08"] == Decimal(80)

    def test_8pct_per_line_ineligible_blocked(self):
        svc = _svc()
        with pytest.raises(ValueError, match="không áp dụng"):
            svc.create_invoice(
                company_id=COMPANY,
                customer_name="KH",
                issue_date=date(2026, 8, 10),
                vat_rate=Decimal("0.1"),
                items=[
                    {
                        "account_code": "5111",
                        "amount": "1000",
                        "vat_rate": "0.08",
                        "category": "telecom",
                    }
                ],
                actor=uuid4(),
                reason="bad",
            )

    def test_8pct_expired_blocked(self):
        from src.bricks.system_settings.rate_windows import SEED_TAX_RATE_WINDOWS, make_rate_gate

        gate = make_rate_gate(SEED_TAX_RATE_WINDOWS)
        svc = InvoiceService(
            fy=FakeFY(),
            coa=FakeCOA(),
            numbering=FakeNumbering(),
            terms=FakeTerms(),
            audit=None,
            rate_gate=gate,
        )
        with pytest.raises(ValueError, match="hết hiệu lực"):
            svc.create_invoice(
                company_id=COMPANY,
                customer_name="KH",
                issue_date=date(2027, 1, 5),
                vat_rate=Decimal("0.08"),
                items=[{"account_code": "5111", "amount": "1000", "vat_rate": "0.08"}],
                actor=uuid4(),
                reason="expired",
            )


class TestFX:
    def test_fx_requires_rate(self):
        svc = _svc()
        with pytest.raises(ValueError, match="fx_rate required"):
            svc.create_invoice(
                company_id=COMPANY,
                customer_name="KH",
                issue_date=date(2026, 8, 10),
                vat_rate=Decimal("0.1"),
                items=[{"account_code": "5111", "amount": "1000"}],
                currency_code="USD",
                actor=uuid4(),
                reason="fx",
            )

    def test_fx_persists(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "25400000"}],
            currency_code="USD",
            fx_rate="25400",
            actor=uuid4(),
            reason="fx ok",
        )
        assert inv.currency_code == "USD"
        assert inv.fx_rate == Decimal(25400)


class TestDeduction:
    def test_deduction_needs_posted(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "1000000"}],
            actor=uuid4(),
            reason="a",
        )
        with pytest.raises(ValueError, match="POSTED"):
            svc.create_deduction(
                inv.id,
                deduction_type="RETURN",
                amount="100",
                actor=uuid4(),
                reason="r",
                voucher_service=FakeVoucher(),
            )

    def test_deduction_amount_exceeds(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "1000"}],
            actor=uuid4(),
            reason="a",
        )
        from src.bricks.invoice.domain import InvoiceStatus

        inv.status = InvoiceStatus.POSTED
        # need repo save? direct call uses memory repo already
        with pytest.raises(ValueError, match="cannot exceed"):
            svc.create_deduction(
                inv.id,
                deduction_type="RETURN",
                amount="2000",
                actor=uuid4(),
                reason="r",
                voucher_service=FakeVoucher(),
            )

    def test_deduction_happy(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "1000000"}],
            actor=uuid4(),
            reason="a",
        )
        from src.bricks.invoice.domain import InvoiceStatus

        inv.status = InvoiceStatus.POSTED
        fv = FakeVoucher()
        v = svc.create_deduction(
            inv.id,
            deduction_type="RETURN",
            amount="500000",
            actor=uuid4(),
            reason="return",
            voucher_service=fv,
        )
        assert v.number == "PT/000001"
        assert fv.last["lines"][0]["account_code"] == "5212"


class TestTT99:
    def test_bds_defers(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "1000000", "category": "real_estate"}],
            actor=uuid4(),
            reason="bds",
        )
        assert inv.deferred_amount > 0

    def test_multi_po_service_deferred(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[
                {
                    "account_code": "5111",
                    "amount": "1000000",
                    "vat_rate": "0.1",
                    "po_id": "goods-1",
                },
                {
                    "account_code": "5111",
                    "amount": "500000",
                    "vat_rate": "0.1",
                    "po_id": "service-maintenance",
                },
            ],
            actor=uuid4(),
            reason="bundle",
        )
        assert inv.deferred_amount == Decimal(550000)  # 500k + 50k vat

    def test_checksum_hardened(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[{"account_code": "5111", "amount": "1000", "vat_rate": "0.05"}],
            actor=uuid4(),
            reason="a",
        )
        c1 = inv.checksum
        inv2 = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH2",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[{"account_code": "5111", "amount": "1000", "vat_rate": "0.10"}],
            actor=uuid4(),
            reason="a",
        )
        # different vat per line should produce different checksum even if grand differs? check not equal
        assert c1 != inv2.checksum

    def test_einvoice_status_default(self):
        svc = _svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="KH",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.0"),
            items=[{"account_code": "5111", "amount": "1000"}],
            actor=uuid4(),
            reason="a",
        )
        assert inv.einvoice_status == EInvoiceStatus.NOT_ISSUED
