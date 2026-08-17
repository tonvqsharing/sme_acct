"""Hóa đơn chứng từ hàng hóa / dịch vụ theo NĐ 123/2020/NĐ-CP."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.entities.base import InvoiceStatus, InvoiceType, TaxRate


class InvoiceItem:
    """Chi tiết hóa đơn."""

    __slots__ = (
        "product_name",
        "unit",
        "quantity",
        "unit_price",
        "vat_rate",
        "vat_amount",
        "total_amount",
        "discount",
    )

    def __init__(
        self,
        product_name: str,
        quantity: float,
        unit_price: float,
        unit: str = "Cái",
        vat_rate: TaxRate = TaxRate.VAT_10,
        discount: float = 0.0,
    ) -> None:
        self.product_name = product_name.strip()
        self.unit = unit.strip()
        self.quantity = round(quantity, 2)
        self.unit_price = round(unit_price, 2)
        self.vat_rate = vat_rate
        self.discount = round(discount, 2)
        line_total = self.quantity * self.unit_price - self.discount
        self.vat_amount = round(line_total * self.vat_rate.value / 100, 2)
        self.total_amount = round(line_total + self.vat_amount, 2)


class Invoice:
    """Hóa đơn đầu vào / đầu ra theo quy định NĐ 123/2020/NĐ-CP."""

    __slots__ = (
        "id",
        "serial",
        "invoice_number",
        "invoice_type",
        "status",
        "issue_date",
        "partner_id",
        "partner_name",
        "partner_tax_id",
        "payment_method",
        "items",
        "subtotal",
        "vat_total",
        "grand_total",
        "currency",
        "exchange_rate",
        "notes",
        "replaced_by_id",
        "created_at",
        "updated_at",
    )

    def __init__(
        self,
        serial: str,
        invoice_number: str,
        invoice_type: InvoiceType,
        partner_name: str,
        partner_tax_id: str,
        issue_date: date | None = None,
        partner_id: UUID | None = None,
        currency: str = "VND",
        exchange_rate: float = 1.0,
        notes: str = "",
    ) -> None:
        from uuid import uuid4

        self.id: UUID = uuid4()
        self.serial = serial.strip()
        self.invoice_number = invoice_number.strip()
        self.invoice_type = invoice_type
        self.status = InvoiceStatus.DRAFT
        self.issue_date = issue_date or date.today()
        self.partner_id = partner_id
        self.partner_name = partner_name.strip()
        self.partner_tax_id = partner_tax_id.strip()
        self.payment_method = ""
        self.items: list[InvoiceItem] = []
        self.subtotal: float = 0.0
        self.vat_total: float = 0.0
        self.grand_total: float = 0.0
        self.currency = currency.upper()
        self.exchange_rate = exchange_rate
        self.notes = notes.strip()
        self.replaced_by_id: UUID | None = None
        self.created_at: date = date.today()
        self.updated_at: date = date.today()

    def add_item(self, item: InvoiceItem) -> None:
        self.items.append(item)
        self._recalculate()

    def _recalculate(self) -> None:
        self.subtotal = round(sum(i.quantity * i.unit_price - i.discount for i in self.items), 2)
        self.vat_total = round(sum(i.vat_amount for i in self.items), 2)
        self.grand_total = round(self.subtotal + self.vat_total, 2)
        self.updated_at = date.today()

    def approve(self) -> None:
        if self.status != InvoiceStatus.DRAFT:
            raise ValueError(f"Không thể duyệt hóa đơn ở trạng thái {self.status.value}")
        self.status = InvoiceStatus.APPROVED
        self.updated_at = date.today()

    def cancel(self, replaced_by: Invoice | None = None) -> None:
        if self.status in (InvoiceStatus.CANCELLED, InvoiceStatus.REPLACED):
            raise ValueError("Hóa đơn đã huỷ hoặc đã thay thế")
        self.status = InvoiceStatus.CANCELLED
        if replaced_by:
            self.replaced_by_id = replaced_by.id
            self.status = InvoiceStatus.REPLACED
        self.updated_at = date.today()

    def __repr__(self) -> str:
        return f"Invoice({self.serial}-{self.invoice_number!r}, {self.status.value})"
