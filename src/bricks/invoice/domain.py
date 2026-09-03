"""Invoice domain — pure Python. Misa/Fast/Bravo parity, TT99/NĐ254 compliant."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


class InvoiceStatus(Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"


class EInvoiceStatus(Enum):
    NOT_ISSUED = "NOT_ISSUED"
    SIGNED = "SIGNED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class DeductionType(Enum):
    RETURN = "RETURN"  # 5211 — hàng bán bị trả lại
    DISCOUNT = "DISCOUNT"  # 5212 — giảm giá hàng bán
    REBATE = "REBATE"  # 5213 — chiết khấu thương mại


@dataclass
class InvoiceItem:
    account_code: str
    description: str
    amount: Decimal
    vat_rate: Decimal | None = None  # None → fallback to Invoice.vat_rate (legacy)
    category: str | None = None  # for 8% eligibility
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    po_id: str | None = None  # performance obligation id (TT99 multi-PO)
    is_agent: bool = False  # principal vs agent lane


@dataclass
class Invoice:
    company_id: UUID
    number: str
    issue_date: date
    customer_name: str
    items: list[InvoiceItem]
    vat_rate: Decimal = Decimal("0.1")  # legacy header rate, fallback
    due_date: date | None = None
    payment_term_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    checksum: str = ""
    # NĐ254 e-invoice fields
    template_code: str = ""  # ký hiệu mẫu số e.g. 1C26TAA
    invoice_symbol: str = ""  # ký hiệu HĐ e.g. HD/
    customer_mst: str | None = None
    currency_code: str = "VND"
    fx_rate: Decimal | None = None
    amount_original: Decimal | None = None  # FX original total
    einvoice_status: EInvoiceStatus = EInvoiceStatus.NOT_ISSUED
    # TT99 deferral
    deferred_amount: Decimal = Decimal(0)  # portion deferred to 3387

    @property
    def subtotal(self) -> Decimal:
        return sum((i.amount for i in self.items), Decimal(0))

    def _item_vat_rate(self, item: InvoiceItem) -> Decimal:
        if item.vat_rate is not None:
            return item.vat_rate
        return self.vat_rate

    @property
    def vat_breakdown(self) -> dict[str, Decimal]:
        """Map fraction string → summed VAT (VND, quantize 1)."""
        out: dict[str, Decimal] = {}
        for it in self.items:
            rate = self._item_vat_rate(it)
            # NOT_TAXED -1 → 0 VAT
            eff_rate = Decimal(0) if rate == Decimal(-1) else rate
            vat = (it.amount * eff_rate).quantize(Decimal(1))
            key = str(rate) if rate is not None else str(self.vat_rate)
            # normalize: Decimal string without trailing zeros? keep as is for catalog match
            # use str(rate) canonical
            out[key] = out.get(key, Decimal(0)) + vat
        return out

    @property
    def vat_amount(self) -> Decimal:
        return sum(self.vat_breakdown.values(), Decimal(0))

    @property
    def grand_total(self) -> Decimal:
        return self.subtotal + self.vat_amount

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        # Hardened: canonical items + breakdown + status (not just grand_total)
        canonical = json.dumps(
            [
                {
                    "account_code": i.account_code,
                    "amount": str(i.amount),
                    "vat_rate": str(i.vat_rate) if i.vat_rate is not None else str(self.vat_rate),
                    "category": i.category or "",
                }
                for i in sorted(self.items, key=lambda x: (x.account_code, str(x.amount)))
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
        breakdown = json.dumps(
            {k: str(v) for k, v in sorted(self.vat_breakdown.items())},
            sort_keys=True,
            ensure_ascii=False,
        )
        payload = f"{prev}{self.id}{actor}{self.status.value}{self.einvoice_status.value}{canonical}{breakdown}{self.grand_total}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()
