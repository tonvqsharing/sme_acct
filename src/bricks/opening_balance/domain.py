"""Opening balance domain — pure Python. Day-one balances, locked at go-live."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64
TOLERANCE = Decimal("0.01")


class BatchSource(Enum):
    MANUAL = "MANUAL"
    EXCEL = "EXCEL"
    YEAR_ROLL = "YEAR_ROLL"


class BatchState(Enum):
    DRAFT = "DRAFT"
    LOCKED = "LOCKED"


@dataclass
class OpeningBatch:
    company_id: UUID
    fiscal_year_id: UUID
    source: BatchSource = BatchSource.MANUAL
    state: BatchState = BatchState.DRAFT
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.state.value}{self.source.value}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class GLBalance:
    batch_id: UUID
    account_code: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
    currency_code: str = "VND"
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.account_code.strip():
            raise ValueError("account_code required")
        if self.debit < 0 or self.credit < 0:
            raise ValueError("amounts must be non-negative")
        if (self.debit > 0) == (self.credit > 0):
            raise ValueError("exactly one side must be positive")


@dataclass
class BankOpening:
    batch_id: UUID
    bank_account_id: UUID
    amount: Decimal = Decimal(0)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("amount must be non-negative")


@dataclass
class CounterpartyBalance:
    batch_id: UUID
    account_code: str
    party_id: UUID
    side: str  # "debit" | "credit"
    amount: Decimal = Decimal(0)
    proof: bool = False
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.account_code.strip():
            raise ValueError("account_code required")
        if self.side not in ("debit", "credit"):
            raise ValueError("side must be debit or credit")
        if self.amount <= 0:
            raise ValueError("amount must be > 0")
