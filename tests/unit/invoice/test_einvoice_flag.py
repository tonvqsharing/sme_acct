"""TDD RED — Slice 3a: sales_e_invoice_enabled panel flag."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.invoice.domain import EInvoiceStatus, Invoice, InvoiceItem, InvoiceStatus
from src.bricks.invoice.services import EInvoiceDisabledError, InvoiceService

COMPANY = uuid4()


def _posted_invoice():
    items = [
        InvoiceItem(
            account_code="5111", description="Bán", amount=Decimal(1000), vat_rate=Decimal("0.1")
        )
    ]
    inv = Invoice(
        company_id=COMPANY,
        number="HD/000001",
        issue_date=date(2026, 8, 10),
        customer_name="KH",
        template_code="1C26TAA",
        invoice_symbol="HD/",
        items=items,
        status=InvoiceStatus.POSTED,
    )
    return inv


class FakeRepo:
    def __init__(self, inv):
        self._inv = inv

    def get_by_id(self, iid):
        return self._inv if self._inv and self._inv.id == iid else None

    def save(self, inv):
        self._inv = inv
        return inv


def _svc(inv, **kw):
    return InvoiceService(
        fy=None, coa=None, numbering=None, terms=None, audit=None, repo=FakeRepo(inv), **kw
    )


def test_issue_blocked_when_flag_off():
    inv = _posted_invoice()
    svc = _svc(inv, einvoice_enabled_of=lambda cid: False)
    with pytest.raises(EInvoiceDisabledError):
        svc.issue_einvoice(inv.id, actor=uuid4(), reason="x")


def test_issue_allowed_when_flag_on():
    inv = _posted_invoice()
    svc = _svc(inv, einvoice_enabled_of=lambda cid: True)
    out = svc.issue_einvoice(inv.id, actor=uuid4(), reason="ok")
    assert out.einvoice_status == EInvoiceStatus.SENT


def test_issue_allowed_by_default_without_port():
    inv = _posted_invoice()
    svc = _svc(inv)
    out = svc.issue_einvoice(inv.id, actor=uuid4(), reason="ok")
    assert out.einvoice_status == EInvoiceStatus.SENT
