"""Invoice domain — pure Python."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


class InvoiceStatus(Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"


@dataclass
class InvoiceItem:
    account_code: str
    description: str
    amount: Decimal


@dataclass
class Invoice:
    company_id: UUID
    number: str
    issue_date: date
    customer_name: str
    items: list[InvoiceItem]
    vat_rate: Decimal
    due_date: date | None = None
    payment_term_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    checksum: str = ""

    @property
    def subtotal(self) -> Decimal:
        return sum((i.amount for i in self.items), Decimal(0))

    @property
    def vat_amount(self) -> Decimal:
        return (self.subtotal * self.vat_rate).quantize(Decimal(1))

    @property
    def grand_total(self) -> Decimal:
        return self.subtotal + self.vat_amount

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.status.value}" f"{self.grand_total}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()
