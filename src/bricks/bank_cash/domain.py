"""Bank & Cash accounts domain. Pure Python. Per specs-bank-cash-accounts.md."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64

CASH_CODE_RE = re.compile(r"^[1-9]\d{2}$|^[1-9]\d{3}$")  # TT99/TT133 format


def chain_checksum(prev: str, entity_id: UUID, actor: UUID, reason: str) -> str:
    payload = f"{prev}{entity_id}{actor}{reason}"
    return hashlib.sha256(payload.encode()).hexdigest()


class BankAccountStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class CashAccountStatus(Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    CLOSED = "closed"


@dataclass
class BankAccount:
    company_id: UUID
    bank_name: str
    account_number: str
    account_holder: str
    branch: str = ""
    is_primary: bool = False
    id: UUID = field(default_factory=uuid4)
    status: BankAccountStatus = BankAccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.bank_name.strip():
            raise ValueError("bank_name is required")
        if not self.account_number.strip():
            raise ValueError("account_number is required")
        if len(self.account_number) > 30:
            raise ValueError("account_number must be <= 30 chars")
        if not self.account_holder.strip():
            raise ValueError("account_holder is required")


@dataclass
class CashAccount:
    company_id: UUID
    code: str
    name: str
    opening_balance: Decimal = Decimal(0)
    current_balance: Decimal = Decimal(0)
    is_system: bool = False
    id: UUID = field(default_factory=uuid4)
    status: CashAccountStatus = CashAccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not CASH_CODE_RE.match(self.code or ""):
            raise ValueError(f"code must match ^[1-9]\\d{{2}}$|^[1-9]\\d{{3}}$, got '{self.code}'")
        if not self.name.strip():
            raise ValueError("name is required")

    def apply_delta(self, amount: Decimal) -> None:
        """Caller enforces the negative-balance approval rule."""
        self.current_balance += amount
