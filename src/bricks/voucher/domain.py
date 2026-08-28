"""Voucher (chứng từ) domain — double-entry journal. Pure Python."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

TOLERANCE = Decimal("0.01")  # docs/CODING_CONVENTION §5: cân đối trong 0.01
GENESIS_CHECKSUM = "0" * 64


class VoucherStatus(Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"


class CashFlowClass(Enum):
    """Cash flow activity classification per TT99 B03-DN.

    OPERATING: day-to-day business activities
    INVESTING: buying/selling long-term assets
    FINANCING: borrowings, equity, dividends
    """

    OPERATING = "operating"
    INVESTING = "investing"
    FINANCING = "financing"


@dataclass
class JournalLine:
    account_code: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
    bank_account_id: UUID | None = None
    currency_code: str | None = None
    fx_rate: Decimal | None = None
    amount_original: Decimal | None = None
    cash_flow_class: CashFlowClass | None = None

    def __post_init__(self) -> None:
        if self.debit > 0 and self.credit > 0:
            raise ValueError("line must have exactly one side")
        if self.debit < 0 or self.credit < 0:
            raise ValueError("amounts must be non-negative")


@dataclass
class Voucher:
    company_id: UUID
    number: str
    entry_date: date
    description: str
    lines: list[JournalLine]
    id: UUID = field(default_factory=uuid4)
    status: VoucherStatus = VoucherStatus.DRAFT
    checksum: str = ""

    @property
    def total_debit(self) -> Decimal:
        return sum((l.debit for l in self.lines), Decimal(0))

    @property
    def total_credit(self) -> Decimal:
        return sum((l.credit for l in self.lines), Decimal(0))

    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debit - self.total_credit) <= TOLERANCE

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.status.value}{self.number}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()
