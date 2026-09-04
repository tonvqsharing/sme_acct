"""TDD RED — Slice7: GDT XML builder + service issue (mock signer, no 3P)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.invoice.domain import EInvoiceStatus, Invoice, InvoiceItem, InvoiceStatus
from src.bricks.invoice.einvoice import build_einvoice_xml, validate_einvoice_ready
from src.bricks.invoice.services import (
    AlreadyIssuedError,
    InvoiceService,
    NotPostedError,
)

COMPANY = uuid4()


def _invoice(**over):
    items = [
        InvoiceItem(
            account_code="5111",
            description="Bán hàng",
            amount=Decimal(10000000),
            vat_rate=Decimal("0.1"),
        )
    ]
    base = {
        "company_id": COMPANY,
        "number": "HD/000001",
        "issue_date": date(2026, 8, 10),
        "customer_name": "Cty Khách",
        "customer_mst": "0101234567",
        "template_code": "1C26TAA",
        "invoice_symbol": "HD/",
        "items": items,
    }
    base.update(over)
    return Invoice(**base)


def test_build_xml_round_trips_through_gdt_parser():
    from src.bricks.xml_ingest.domain import parse_xml_invoice

    inv = _invoice(status=InvoiceStatus.POSTED)
    xml_str = build_einvoice_xml(inv, seller={"name": "Cty Bán", "mst": "0107654321"})
    parsed = parse_xml_invoice(xml_str.encode())
    assert parsed.invoice_number == "HD/000001"
    assert parsed.buyer_mst == "0101234567"
    assert parsed.template_code == "1C26TAA"


def test_build_xml_escapes_special_chars():
    inv = _invoice(customer_name="Cty <A> & B")
    xml_str = build_einvoice_xml(inv, seller={"name": "S", "mst": "0107654321"})
    ET.fromstring(xml_str.encode())  # must stay well-formed
    assert "&lt;A&gt;" in xml_str


def test_validate_rejects_draft():
    with pytest.raises(NotPostedError):
        validate_einvoice_ready(_invoice(status=InvoiceStatus.DRAFT))


def test_validate_rejects_already_issued():
    with pytest.raises(AlreadyIssuedError):
        validate_einvoice_ready(
            _invoice(status=InvoiceStatus.POSTED, einvoice_status=EInvoiceStatus.SENT)
        )


def test_validate_rejects_missing_template():
    with pytest.raises(ValueError, match="template"):
        validate_einvoice_ready(_invoice(status=InvoiceStatus.POSTED, template_code=""))


class FakeRepo:
    def __init__(self, inv):
        self._inv = inv

    def get_by_id(self, iid):
        return self._inv if self._inv and self._inv.id == iid else None

    def save(self, inv):
        self._inv = inv
        return inv


class FakeAudit:
    def __init__(self):
        self.entries: list = []

    def append(self, **kw):
        self.entries.append(kw)


def _svc(inv):
    return InvoiceService(
        fy=None,
        coa=None,
        numbering=None,
        terms=None,
        audit=FakeAudit(),
        repo=FakeRepo(inv),
    )


def test_service_issue_sets_sent_with_xml_hash():
    inv = _invoice(status=InvoiceStatus.POSTED)
    svc = _svc(inv)
    out = svc.issue_einvoice(
        inv.id, actor=uuid4(), reason="phat hanh", seller={"name": "Cty Bán", "mst": "0107654321"}
    )
    assert out.einvoice_status == EInvoiceStatus.SENT
    entry = svc._audit.entries[-1]
    assert entry["action"] == "EINVOICE_ISSUE"
    assert entry["after_value"]["xml_hash"]
    assert entry["after_value"]["signature"]


def test_service_issue_double_raises():
    inv = _invoice(status=InvoiceStatus.POSTED, einvoice_status=EInvoiceStatus.SENT)
    svc = _svc(inv)
    with pytest.raises(AlreadyIssuedError):
        svc.issue_einvoice(inv.id, actor=uuid4(), reason="again")


def test_service_issue_requires_posted():
    inv = _invoice(status=InvoiceStatus.DRAFT)
    svc = _svc(inv)
    with pytest.raises(NotPostedError):
        svc.issue_einvoice(inv.id, actor=uuid4(), reason="x")
