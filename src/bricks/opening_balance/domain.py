"""Opening balance domain — pure Python. Day-one balances, locked at go-live."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
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


@dataclass
class AssetOpening:
    """TSCĐ/CCDC opening row: book state at go-live (kind=fixed_asset)."""

    batch_id: UUID
    kind: str  # fixed_asset (ccdc arrives S4b)
    code: str
    name: str
    original_cost: Decimal
    remaining_value: Decimal
    months_left: int
    expense_account: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.original_cost <= 0:
            raise ValueError(f"original_cost must be > 0, got {self.original_cost}")
        if not 0 <= self.remaining_value <= self.original_cost:
            raise ValueError(
                f"remaining_value must be within [0, original_cost], got {self.remaining_value}"
            )
        if self.months_left < 1:
            raise ValueError(f"months_left must be >= 1, got {self.months_left}")


@dataclass
class StockOpening:
    batch_id: UUID
    product_id: UUID
    warehouse_id: UUID
    qty: Decimal = Decimal(0)
    total_value: Decimal = Decimal(0)
    lot_code: str | None = None
    expiry_date: date | None = None
    receipt_date: date | None = None
    receipt_doc: str | None = None
    unit_cost: Decimal | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError("qty must be > 0")
        if self.total_value < 0:
            raise ValueError("total_value must be >= 0")
