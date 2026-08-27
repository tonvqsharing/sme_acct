"""Unit tests for xml_ingest services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.bricks.xml_ingest.services import XMLIngestService

# ─── Fake purchase service ──────────────────────────────────────────────


@dataclass
class _FakeSupplierInvoice:
    id: UUID
    total_payment: Decimal


class FakePurchaseService:
    """Minimal stub that records calls and returns a fake SupplierInvoice."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._next_id: UUID = uuid4()
        self._fail: str | None = None

    def set_fail(self, msg: str) -> None:
        self._fail = msg

    def create_invoice(self, **kwargs: Any) -> _FakeSupplierInvoice:
        if self._fail:
            raise ValueError(self._fail)
        self.calls.append(kwargs)
        return _FakeSupplierInvoice(id=self._next_id, total_payment=Decimal(1100000))


# ─── Sample XML fixtures ────────────────────────────────────────────────

GOOD_XML = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon>
  <HDon>
    <SHDon>00001234</SHDon>
    <KHMSHDon>AA</KHMSHDon>
    <KMHHDON>1</KMHHDON>
    <NLap>2026-08-15</NLap>
    <NBan>
      <Ten>ABC Company</Ten>
      <MST>0123456789</MST>
    </NBan>
    <NMua>
      <Ten>XYZ Buyer</Ten>
      <MST>9876543210</MST>
    </NMua>
    <HHDVu>
      <HH>
        <Ten>Van phong pham</Ten>
        <DVTinh>cai</DVTinh>
        <SLuong>100</SLuong>
        <DGia>20000</DGia>
        <ThTien>2000000</ThTien>
        <TSuat>10</TSuat>
      </HH>
    </HHDVu>
    <TongCong>2200000</TongCong>
  </HDon>
</DLHDon>
"""

NO_LINES_XML = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon>
  <HDon>
    <SHDon>EMPTY-001</SHDon>
    <NBan><MST>123</MST></NBan>
  </HDon>
</DLHDon>
"""


# ─── Tests ───────────────────────────────────────────────────────────────


class TestIngestSingle:
    def test_success(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            default_expense_account="6421001",
            entry_date="2026-08-20",
            actor_id=str(uuid4()),
            reason="test ingest",
        )
        assert result.success is True
        assert result.invoice_number == "00001234"
        assert result.supplier_name == "ABC Company"
        assert result.supplier_mst == "0123456789"
        assert result.total_after_vat == "1100000"
        assert len(fake.calls) == 1
        call = fake.calls[0]
        assert call["supplier_name"] == "ABC Company"
        assert call["supplier_mst"] == "0123456789"
        assert call["invoice_number"] == "00001234"
        assert call["invoice_date"] == date(2026, 8, 15)
        assert call["entry_date"] == date(2026, 8, 20)
        assert len(call["lines"]) == 1
        assert call["lines"][0]["expense_account"] == "6421001"

    def test_missing_actor(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            actor_id="",
            reason="test",
        )
        assert result.success is False
        assert "actor_id" in result.error

    def test_missing_reason(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            actor_id=str(uuid4()),
            reason="",
        )
        assert result.success is False
        assert "reason" in result.error

    def test_malformed_xml(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=b"<not valid xml",
            actor_id=str(uuid4()),
            reason="test",
        )
        assert result.success is False
        assert "XML" in result.error

    def test_no_lines(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=NO_LINES_XML,
            actor_id=str(uuid4()),
            reason="test",
        )
        assert result.success is False
        assert "No line items" in result.error
        assert len(fake.calls) == 0

    def test_purchase_service_failure(self):
        fake = FakePurchaseService()
        fake.set_fail("Duplicate invoice")
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            default_expense_account="6421001",
            actor_id=str(uuid4()),
            reason="test",
        )
        assert result.success is False
        assert "Duplicate invoice" in result.error
        assert result.invoice_number == "00001234"

    def test_default_entry_date_is_today(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            default_expense_account="6421001",
            actor_id=str(uuid4()),
            reason="test",
        )
        assert result.success is True
        call = fake.calls[0]
        assert call["entry_date"] == date.today()  # noqa: DTZ011 — test asserts "today"

    def test_warning_when_no_expense_account(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_single(
            company_id=str(uuid4()),
            xml_bytes=GOOD_XML,
            default_expense_account="",
            actor_id=str(uuid4()),
            reason="test",
        )
        assert result.success is True
        assert any("expense_account" in w for w in result.warnings)


class TestIngestBatch:
    def test_batch_success(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        files = [
            {"filename": "inv1.xml", "content": GOOD_XML},
            {"filename": "inv2.xml", "content": GOOD_XML},
        ]
        result = svc.ingest_batch(
            company_id=str(uuid4()),
            files=files,
            default_expense_account="6421001",
            actor_id=str(uuid4()),
            reason="batch test",
        )
        assert result.total_files == 2
        assert result.success_count == 2
        assert result.error_count == 0
        assert len(fake.calls) == 2

    def test_batch_mixed(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        files = [
            {"filename": "good.xml", "content": GOOD_XML},
            {"filename": "bad.xml", "content": b"<broken>"},
        ]
        result = svc.ingest_batch(
            company_id=str(uuid4()),
            files=files,
            default_expense_account="6421001",
            actor_id=str(uuid4()),
            reason="batch mixed",
        )
        assert result.total_files == 2
        assert result.success_count == 1
        assert result.error_count == 1
        assert result.results[0].success is True
        assert result.results[1].success is False

    def test_batch_empty(self):
        fake = FakePurchaseService()
        svc = XMLIngestService(purchase_service=fake)
        result = svc.ingest_batch(
            company_id=str(uuid4()),
            files=[],
            actor_id=str(uuid4()),
            reason="empty",
        )
        assert result.total_files == 0
        assert result.success_count == 0
