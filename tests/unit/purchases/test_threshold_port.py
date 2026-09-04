"""TDD RED — Slice 2a: non_cash_threshold port (config panel value wins)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.bricks.purchases.services import PurchaseService

COMPANY = uuid4()


class FakeFY:
    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        return None


class FakeRepo:
    def __init__(self):
        self.saved = None

    def exists_duplicate(self, cid, mst, number, symbol):
        return False

    def create(self, inv):
        self.saved = inv
        return inv


def _body(**over):
    base = {
        "company_id": COMPANY,
        "supplier_name": "NCC A",
        "supplier_mst": "0101234567",
        "invoice_number": "0000001",
        "invoice_symbol": "1C26TAA",
        "invoice_date": date(2026, 8, 10),
        "entry_date": date(2026, 8, 10),
        "payment_method": "cash",
        "payment_proof": False,
        "lines": [
            {
                "expense_account": "1521",
                "description": "NVL",
                "amount_pre_vat": "6000000",
                "vat_rate": "0.1",
            }
        ],
    }
    base.update(over)
    return base


def _svc(**kw):
    return PurchaseService(repo=FakeRepo(), fy=FakeFY(), coa=FakeCOA(), **kw)


def test_config_threshold_overrides_default():
    svc = _svc(threshold_of=lambda cid: Decimal(10000000))
    inv = svc.create_invoice(actor=uuid4(), reason="buy", **_body())
    # 6.6tr < 10tr panel value → proof not required → DEDUCTIBLE
    assert inv.deductibility.value == "DEDUCTIBLE"
    assert inv.non_cash_threshold == Decimal(10000000)


def test_default_threshold_unchanged_without_port():
    svc = _svc()
    inv = svc.create_invoice(actor=uuid4(), reason="buy", **_body())
    # 6.6tr ≥ 5tr default, cash, no proof → NON_DEDUCTIBLE
    assert inv.deductibility.value == "NON_DEDUCTIBLE"
    assert inv.non_cash_threshold == Decimal(5000000)
