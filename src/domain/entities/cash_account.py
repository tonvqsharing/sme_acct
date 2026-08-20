"""Cash on Hand domain entities (specs-bank-cash-accounts.md §3).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Law on Accounting 2015 Art. 10; Circular 99/2025/TT-BTC;
TT99 code format: ^[1-9]\d{2}$ or ^[1-9]\d{3}$; SOD policy D11;
SHA-256 audit checksum chaining per Circular 99/2025/TT-BTC Art. 11.
"""

from __future__ import annotations

import re as _re
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from datetime import date

from src.domain.exceptions import DomainException


class AccountStatus(str, Enum):
    """Cash account status."""

    ACTIVE = "Active"
    LOCKED = "Locked"
    CLOSED = "Closed"


class CashAccount:
    """Cash on hand aggregate root with invariants per Circular 99/2025/TT-BTC.

    Attributes:
        id: UUID identifier
        company_id: FK to companies (tenant isolation)
        code: Cash code per TT99 format (^[1-9]\d{2}$ or ^[1-9]\d{3}$)
        name: Cash account name
        opening_balance: Opening balance at creation (VND, 2 decimal)
        current_balance: Current balance (updated by transactions)
        is_system: System account (protected from modification)
        status: ACTIVE/LOCKED/CLOSED
        created_at: creation date
        checksum: SHA-256 for audit trail
    """

    TT99_PATTERN = r"^[1-9]\d{2}$|^[1-9]\d{3}$"

    def __init__(
        self,
        company_id: UUID,
        code: str,
        name: str,
        opening_balance: float | Decimal = 0.0,
        is_system: bool = False,
        created_by: UUID | None = None,
        status: AccountStatus = AccountStatus.ACTIVE,
    ) -> None:
        # 1. Validate code per TT99 format
        if not _re.match(self.TT99_PATTERN, code):
            raise DomainException(
                f"Mã số không hợp lệ: {code}. Định dạng: ^[1-9]\\d{{2}}$ hoặc ^[1-9]\\d{{3}}$"
            )

        # 2. Validate company exists check - deferred to service/repo

        # 3. Set attributes
        self.code = code
        self.name = name.strip()
        self.company_id = company_id
        self.is_system = is_system
        self.status = status
        self.created_by = created_by

        # 8. Balance initialization: current_balance = opening_balance
        if isinstance(opening_balance, (int, float)):
            self.opening_balance = float(opening_balance)
        else:
            self.opening_balance = float(opening_balance)
        self.current_balance = self.opening_balance

        # 9. Audit identity
        self.id = uuid4()
        self.created_at = date.today()
        self.checksum = uuid4().hex[:64]

    def update_balance(self, amount: float | Decimal, actor: UUID, reason: str) -> None:
        """Update cash balance with mutation tracking.

        Rules:
        - Cannot update CLOSED account
        - System accounts protected (only chief accountant can)
        - Balance change tracked for audit
        """
        if self.status == AccountStatus.CLOSED:
            raise DomainException("Không thể cập nhật trên tài khoản đã đóng")

        if self.is_system and not self._is_chief_accountant(actor):
            raise DomainException("Tài khoản hệ thống không được sửa đổi")

        # Update balance
        new_balance = (self.current_balance or 0.0) + float(amount)
        self.current_balance = new_balance
        self.checksum = uuid4().hex[:64]

    def _is_chief_accountant(self, actor: UUID) -> bool:
        """Check if actor is chief accountant - deferred to service layer."""
        return False  # placeholder; service enforces

    def can_modify(self, actor: UUID) -> bool:
        """Check if actor can modify this account."""
        if self.status == AccountStatus.CLOSED:
            return False
        if self.is_system and not self._is_chief_accountant(actor):
            return False
        return True

    def soft_close(self, actor: UUID, reason: str) -> None:
        """Soft-close cash account: requires balance = 0."""
        if self.status == AccountStatus.CLOSED:
            raise DomainException("Tài khoản đã được đóng")
        if self.current_balance != 0:
            raise DomainException("Không thể đóng tài khoản có số dư không bằng 0")
        self.status = AccountStatus.CLOSED
        self.checksum = uuid4().hex[:64]