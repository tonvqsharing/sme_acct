"""Chart of Accounts domain — Vietnamese TT200/TT133 codes. Pure Python."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

# Mã tài khoản: 3 hoặc 4 chữ số, không bắt đầu bằng 0 (Thông tư 200/133)
ACCOUNT_CODE_PATTERN = r"^[1-9]\d{2}$|^[1-9]\d{3}$"
CODE_RE = re.compile(ACCOUNT_CODE_PATTERN)


class AccountStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class NormalBalance(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class Account:
    company_id: UUID
    code: str
    name: str
    normal_balance: NormalBalance = NormalBalance.DEBIT
    parent_code: str | None = None
    id: UUID = field(default_factory=__import__("uuid").uuid4)
    status: AccountStatus = AccountStatus.ACTIVE

    def __post_init__(self) -> None:
        if not CODE_RE.match(self.code or ""):
            raise ValueError(f"code must match {ACCOUNT_CODE_PATTERN}, got '{self.code}'")
        if not self.name or not self.name.strip():
            raise ValueError("name is required")
        if self.parent_code is not None and not CODE_RE.match(self.parent_code):
            raise ValueError("parent_code must be a valid account code")

    @property
    def is_detail(self) -> bool:
        """4-digit accounts are posting-level; 3-digit are aggregates."""
        return len(self.code) == 4
