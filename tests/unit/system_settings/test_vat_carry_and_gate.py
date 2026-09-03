"""P0 8% category gate + VAT carry persistence — added 2026-09-03."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.invoice.services import InvoiceService
from src.bricks.purchases.services import PurchaseService
from src.bricks.system_settings.rate_windows import EXCLUDED_FROM_8PCT, is_8pct_eligible
from src.bricks.system_settings.services import InvalidPeriodError, VatDeclarationService

COMPANY = uuid4()


# ── fakes ────────────────────────────────────────────────────────────────
class FakeFY:
    def find_open_period(self, cid, d):
        return object()


class FakeCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        return None


class FakeNumbering:
    def __init__(self):
        self.seq = 1

    def issue(self, cid):
        n = f"HD/{self.seq:06d}"
        self.seq += 1
        return n


class FakeTerms:
    def get_default(self, cid):
        t = type("T", (), {})()
        t.id = uuid4()
        t.due_days = 30
        return t


class FakeCarry:
    def __init__(self):
        self.store: dict[tuple, Decimal] = {}
        self.prev: dict[tuple, Decimal] = {}

    def get_previous_carry(self, cid, year, month, quarter):
        # simple: return stored prev for that period type
        if quarter is not None:
            key = (str(cid), year, None, quarter - 1 if quarter > 1 else None)
            if quarter == 1:
                key = (str(cid), year - 1, None, 4)
            return self.store.get(key, Decimal(0))
        if month is not None:
            key = (str(cid), year, month - 1 if month > 1 else None, None)
            if month == 1:
                key = (str(cid), year - 1, 12, None)
            return self.store.get(key, Decimal(0))
        return Decimal(0)

    def save_carry(self, cid, year, month, quarter, amount):
        self.store[(str(cid), year, month, quarter)] = amount

    def get_carry(self, cid, year, month, quarter):
        return self.store.get((str(cid), year, month, quarter), Decimal(0))


class FakeConfig:
    def __init__(self, cycle):
        self.vat_settlement_cycle = cycle

    # for repo.get_config
    def get_config(self, cid):
        return FakeConfig(self.vat_settlement_cycle)  # type: ignore[return-value]


class FakeConfigRepo:
    def __init__(self, cycle):
        self.cycle = cycle

    def get_config(self, cid):
        m = type("C", (), {})()
        m.vat_settlement_cycle = self.cycle
        return m


# ── 8% category gate ─────────────────────────────────────────────────────
class TestIs8PctEligible:
    def test_excluded_categories_blocked(self):
        for cat in EXCLUDED_FROM_8PCT:
            assert not is_8pct_eligible(cat)
            assert not is_8pct_eligible(cat.upper())

    def test_unknown_and_empty_allowed(self):
        assert is_8pct_eligible(None)
        assert is_8pct_eligible("")
        assert is_8pct_eligible("manufacturing")


class TestInvoice8PctGate:
    def _svc(self):
        return InvoiceService(
            fy=FakeFY(), coa=FakeCOA(), numbering=FakeNumbering(), terms=FakeTerms(), audit=None
        )

    def test_8pct_telecom_rejected(self):
        svc = self._svc()
        with pytest.raises(ValueError, match="không áp dụng"):
            svc.create_invoice(
                company_id=COMPANY,
                customer_name="X",
                issue_date=date(2026, 8, 10),
                vat_rate=Decimal("0.08"),
                items=[{"account_code": "5111", "amount": "100000", "category": "telecom"}],
                product_category="telecom",
                actor=uuid4(),
                reason="r",
            )

    def test_8pct_second_line_telecom_rejected(self):
        svc = self._svc()
        with pytest.raises(ValueError, match="không áp dụng"):
            svc.create_invoice(
                company_id=COMPANY,
                customer_name="X",
                issue_date=date(2026, 8, 10),
                vat_rate=Decimal("0.08"),
                items=[
                    {"account_code": "5111", "amount": "100000", "category": "manufacturing"},
                    {"account_code": "5111", "amount": "100000", "category": "finance"},
                ],
                actor=uuid4(),
                reason="r",
            )

    def test_8pct_eligible_passes(self):
        svc = self._svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="X",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.08"),
            items=[{"account_code": "5111", "amount": "100000", "category": "manufacturing"}],
            actor=uuid4(),
            reason="r",
        )
        assert inv.vat_amount == Decimal(8000)

    def test_10pct_telecom_allowed(self):
        svc = self._svc()
        inv = svc.create_invoice(
            company_id=COMPANY,
            customer_name="X",
            issue_date=date(2026, 8, 10),
            vat_rate=Decimal("0.1"),
            items=[{"account_code": "5111", "amount": "100000", "category": "telecom"}],
            product_category="telecom",
            actor=uuid4(),
            reason="r",
        )
        assert inv.vat_rate == Decimal("0.1")


class TestPurchase8PctGate:
    def _svc(self):
        class FakeRepo:
            def exists_duplicate(self, *a, **kw):
                return False

            def create(self, inv):
                return inv

        return PurchaseService(
            repo=FakeRepo(),
            fy=FakeFY(),
            coa=FakeCOA(),
            allowed_vat_rates=frozenset({"0", "0.05", "0.08", "0.1"}),
            rate_gate=lambda r, d: True,
        )

    def test_purchase_8pct_finance_rejected(self):
        svc = self._svc()
        with pytest.raises(ValueError, match="không áp dụng"):
            svc.create_invoice(
                company_id=COMPANY,
                supplier_name="NCC",
                supplier_mst="0123456789",
                invoice_number="001",
                invoice_symbol="C25TAA",
                invoice_date=date(2026, 8, 10),
                entry_date=date(2026, 8, 10),
                lines=[
                    {
                        "expense_account": "6421",
                        "amount_pre_vat": "100000",
                        "vat_rate": "0.08",
                        "category": "finance",
                    }
                ],
                actor=uuid4(),
                reason="r",
            )


# ── VAT carry persistence + cycle enforce ────────────────────────────────
class TestVatCarry:
    def test_monthly_carry_added_to_next_month(self):
        carry = FakeCarry()
        carry.store[(str(COMPANY), 2026, 1, None)] = Decimal(500000)
        svc = VatDeclarationService(
            output_source=lambda cid, s, e: [],
            input_source=lambda cid, s, e: [],
            carry_repo=carry,
        )
        d = svc.declare(COMPANY, 2026, month=2)
        assert d["input_vat_deductible"] == Decimal(500000)
        assert d["carry_forward"] == Decimal(500000)

    def test_carry_persisted(self):
        carry = FakeCarry()
        svc = VatDeclarationService(
            output_source=lambda cid, s, e: [
                {"account_code": "3331", "debit": "0", "credit": "100000"}
            ],
            input_source=lambda cid, s, e: [
                {"status": "POSTED", "deductibility": "DEDUCTIBLE", "vat_deductible": "300000"}
            ],
            carry_repo=carry,
        )
        d = svc.declare(COMPANY, 2026, month=3)
        assert d["carry_forward"] == Decimal(200000)
        assert carry.get_carry(COMPANY, 2026, 3, None) == Decimal(200000)

    def test_quarterly_carry_chain(self):
        carry = FakeCarry()
        carry.store[(str(COMPANY), 2026, None, 1)] = Decimal(1000000)
        svc = VatDeclarationService(
            output_source=lambda cid, s, e: [],
            input_source=lambda cid, s, e: [],
            carry_repo=carry,
        )
        d = svc.declare(COMPANY, 2026, quarter=2)
        assert d["input_vat_deductible"] == Decimal(1000000)

    def test_cycle_mismatch_monthly_vs_quarter(self):
        svc = VatDeclarationService(
            output_source=lambda cid, s, e: [],
            input_source=lambda cid, s, e: [],
            config_repo=FakeConfigRepo("monthly"),
        )
        with pytest.raises(InvalidPeriodError, match="tháng"):
            svc.declare(COMPANY, 2026, quarter=1)

    def test_cycle_mismatch_quarterly_vs_month(self):
        svc = VatDeclarationService(
            output_source=lambda cid, s, e: [],
            input_source=lambda cid, s, e: [],
            config_repo=FakeConfigRepo("quarterly"),
        )
        with pytest.raises(InvalidPeriodError, match="quý"):
            svc.declare(COMPANY, 2026, month=5)
