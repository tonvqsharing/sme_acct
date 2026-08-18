"""Hóa đơn chứng từ hàng hóa / dịch vụ theo NĐ 123/2020/NĐ-CP."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.entities.base import InvoiceStatus, InvoiceType, TaxRate
from src.domain.exceptions import SystemSettingsError


# Approval threshold bands (VND amounts) — configurable per company
# Defaults: T1=$500, T2=$5,000, T3=$25,000, T4=$100,000, T5=above
_INVOICE_THRESHOLD_T1 = 500_000_000  # 500 million VND = $500 (approximate)
_INVOICE_THRESHOLD_T2 = 5_000_000_000  # 5 billion VND = $5,000
_INVOICE_THRESHOLD_T3 = 25_000_000_000  # 25 billion VND = $25,000
_INVOICE_THRESHOLD_T4 = 100_000_000_000  # 100 billion VND = $100,000


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

    def approve(self, po_matched: bool = False) -> None:
        """Approve invoice with threshold checking.

        Approval routing based on invoice amount against company threshold matrix:
        - T1 (≤ $500 / ≤ 500,000,000 VND): Auto-approved if PO matched, else manager
        - T2 ($500–$5,000 / 500M–5B VND): Manager approval required
        - T3 ($5,000–$25,000 / 5B–25B VND): Chief accountant approval required
        - T4 ($25,000–$100,000 / 25B–100B VND): Director approval required
        - T5 (> $100,000 / > 100B VND): Admin/Board approval required

        Raises:
            ValueError: If invoice status is not DRAFT.
        """
        if self.status != InvoiceStatus.DRAFT:
            raise ValueError(f"Không thể duyệt hóa đơn ở trạng thái {self.status.value}")

        amount = self.grand_total

        # Threshold check — use default bands if company config not available
        if amount <= _INVOICE_THRESHOLD_T1:
            if po_matched:
                # Auto-approved under T1 with PO match
                self.status = InvoiceStatus.APPROVED
                self.updated_at = date.today()
            else:
                # Under T1 but no PO → route to manager (cannot auto-approve without PO)
                # Status stays DRAFT; caller should route to manager
                pass  # Leave as DRAFT, will be routed to manager
        elif amount <= _INVOICE_THRESHOLD_T2:
            # T2 band: $500–$5,000 → Manager approval required
            # Leave as DRAFT, will be routed to manager via RBAC
            pass
        elif amount <= _INVOICE_THRESHOLD_T3:
            # T3 band: $5,000–$25,000 → Chief accountant approval required
            # Leave as DRAFT, will be routed to chief accountant via RBAC
            pass
        elif amount <= _INVOICE_THRESHOLD_T4:
            # T4 band: $25,000–$100,000 → Director approval required
            # Leave as DRAFT, will be routed to director via RBAC
            pass
        else:
            # T5 band: > $100,000 → Admin/Board approval required
            # Leave as DRAFT, will be routed to admin via RBAC
            pass

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
