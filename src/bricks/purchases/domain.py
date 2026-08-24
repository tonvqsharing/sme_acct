"""Purchase invoice domain — per docs/purchases/specs. Pure Python."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64

NON_CASH_THRESHOLD = Decimal(5000000)  # NĐ 181/2025 Đ.26 (sửa NĐ 144/2026)


class PurchaseStatus(Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class Deductibility(Enum):
    DEDUCTIBLE = "DEDUCTIBLE"
    PENDING_PROOF = "PENDING_PROOF"
    NON_DEDUCTIBLE = "NON_DEDUCTIBLE"


class PaymentMethod(Enum):
    CASH = "cash"
    BANK = "bank"
    NONE = "none"


@dataclass
class SupplierLine:
    expense_account: str
    description: str
    amount_pre_vat: Decimal
    vat_rate: Decimal
    deductible: bool = True

    @property
    def vat_amount(self) -> Decimal:
        return (self.amount_pre_vat * self.vat_rate).quantize(Decimal(1))


@dataclass
class SupplierInvoice:
    company_id: UUID
    supplier_name: str
    supplier_mst: str
    invoice_number: str
    invoice_symbol: str
    invoice_date: date
    entry_date: date
    lines: list[SupplierLine]
    payment_method: PaymentMethod = PaymentMethod.NONE
    payment_proof: bool = False
    id: UUID = field(default_factory=uuid4)
    status: PurchaseStatus = PurchaseStatus.DRAFT
    checksum: str = ""
    created_at: date = field(default_factory=date.today)

    # ── computed totals ────────────────────────────────────────────────
    @property
    def subtotal(self) -> Decimal:
        return sum((l.amount_pre_vat for l in self.lines), Decimal(0))

    @property
    def total_vat(self) -> Decimal:
        return sum((l.vat_amount for l in self.lines), Decimal(0))

    @property
    def total_payment(self) -> Decimal:
        return self.subtotal + self.total_vat

    def _non_cash_proof_ok(self) -> bool:
        """Điều 26 NĐ 181/2025: ≥5tr (gồm VAT) cần chứng từ không tiền mặt."""
        if self.total_payment < NON_CASH_THRESHOLD:
            return True
        if self.payment_method == PaymentMethod.CASH:
            return False
        return self.payment_proof

    def line_effective_deductible(self, line: SupplierLine) -> bool:
        return bool(line.deductible) and self._non_cash_proof_ok()

    @property
    def vat_deductible(self) -> Decimal:
        return sum(
            (l.vat_amount for l in self.lines if self.line_effective_deductible(l)),
            Decimal(0),
        )

    @property
    def vat_non_deductible(self) -> Decimal:
        return self.total_vat - self.vat_deductible

    @property
    def deductibility(self) -> Deductibility:
        if not any(self.line_effective_deductible(l) and l.vat_amount > 0 for l in self.lines):
            if all(not l.deductible for l in self.lines):
                return Deductibility.NON_DEDUCTIBLE
            if (
                not self._non_cash_proof_ok()
                and self.payment_method is PaymentMethod.CASH
                and self.total_payment >= NON_CASH_THRESHOLD
            ):
                return Deductibility.NON_DEDUCTIBLE
            if not self._non_cash_proof_ok() and self.total_vat > 0:
                return Deductibility.PENDING_PROOF
            return Deductibility.NON_DEDUCTIBLE
        if any((not self.line_effective_deductible(l)) and l.deductible for l in self.lines):
            return Deductibility.PENDING_PROOF
        return Deductibility.DEDUCTIBLE

    # ── checksum chain ─────────────────────────────────────────────────
    def compute_checksum(self, prev: str, actor: UUID, action: str, reason: str) -> str:
        payload = (
            f"{prev}{self.id}{actor}{self.status.value}"
            f"{self.invoice_number}{self.invoice_symbol}{action}{reason}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()
