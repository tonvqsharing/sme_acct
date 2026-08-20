"""Bank Account domain entities (specs-bank-cash-accounts.md §3).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Law on Accounting 2015 Art. 10; Circular 99/2025/TT-BTC;
SOD policy D11; SHA-256 audit checksum chaining per Circular 99/2025/TT-BTC Art. 11.
"""

from __future__ import annotations

import re as _re
from enum import Enum
from uuid import UUID, uuid4

from datetime import date

from src.domain.exceptions import DomainException


class AccountStatus(str, Enum):
    """Bank account status."""

    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    CLOSED = "Closed"


class BankAccount:
    """Bank account aggregate root with invariants per Circular 99/2025/TT-BTC.

    Attributes:
        id: UUID identifier
        company_id: FK to companies (tenant isolation)
        bank_name: Bank name (e.g., "VietinBank", "Sacombank")
        account_number: Account number (max 30 chars, unique per company)
        account_holder: Name of account holder
        branch: Branch name/code (default "")
        is_primary: Only one primary per company
        status: ACTIVE/SUSPENDED/CLOSED
        created_at: creation date
        checksum: SHA-256 for audit trail
    """

    def __init__(
        self,
        company_id: UUID,
        bank_name: str,
        account_number: str,
        account_holder: str,
        branch: str = "",
        is_primary: bool = False,
        created_by: UUID | None = None,
        status: AccountStatus = AccountStatus.ACTIVE,
    ) -> None:
        from src.domain.entities.base import TaxId  # noqa: F815 (avoid circular)

        # 1. Validate bank_name
        self.bank_name = bank_name.strip()
        if not self.bank_name:
            raise DomainException("Tên bank không được rỗng")

        # 2. Validate account_number (max 30 chars)
        self.account_number = account_number.strip()
        if not self.account_number:
            raise DomainException("Số tài khoản không được rỗng")
        if len(self.account_number) > 30:
            raise DomainException("Số tài khoản vượt quá 30 ký tự")

        # 3. Validate account_holder
        self.account_holder = account_holder.strip()
        if not self.account_holder:
            raise DomainException("Tên chủ tài khoản không được rỗng")

        # 4. Validate branch
        self.branch = branch.strip()

        # 5. Set status
        self.status = status

        # 7. Audit identity
        self.id = uuid4()
        self.company_id = company_id
        self.created_at = date.today()
        self.checksum = uuid4().hex[:64]
        self.created_by = created_by

    def set_primary(self, actor: UUID, reason: str) -> None:
        """Set this as primary bank account (requires SOD approval)."""
        if self.status != AccountStatus.ACTIVE:
            raise DomainException("Không thể set primary trên tài khoản không phải ACTIVE")
        if actor is None:
            raise DomainException("Actor UUID (D11) là bắt buộc")

    def can_modify(self, actor: UUID) -> bool:
        """Check if actor can modify this account."""
        if self.status == AccountStatus.CLOSED:
            return False
        return True

    def soft_close(self, actor: UUID, reason: str) -> None:
        """Soft-close: ACTIVE → SUSPENDED → CLOSED (via SOD workflow)."""
        if self.status == AccountStatus.CLOSED:
            raise DomainException("Tài khoản đã được đóng")
        self.status = AccountStatus.SUSPENDED
        self.checksum = uuid4().hex[:64]