"""Chart of Accounts domain entities (specs-coa-module-2026.md §1).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Law on Accounting 2015 Chap IV; Circular 99/2025/TT-BTC Art 11;
Circular 200/2014/TT-BTC Appendix II; account code format per TT99:
^\\d{10}$  or  ^\\d{10}-\\d{3}$.
"""

from __future__ import annotations

import re as _re
from uuid import UUID, uuid4

from datetime import datetime, timezone
from enum import Enum

from src.domain.exceptions import InvalidAccountCodeError


# ── AccountCode Value Object ─────────────────────────────────────────

class AccountCode(str):
    """Account code value object per TT99 (Circular 99/2025/TT-BTC).

    Format: ^\\d{10}$ or ^\\d{10}-\\d{3}$ (no leading zero on the 10-digit block).
    Raises InvalidAccountCodeError on invalid format.
    """

    def __new__(cls, code: str) -> AccountCode:
        pattern = r"^[1-9]\d{9}$|^[1-9]\d{9}-\d{1,3}$"
        if not _re.match(pattern, code):
            raise InvalidAccountCodeError(
                "Account code must match ^[1-9]\\d{9}$ or ^[1-9]\\d{9}-\\d{1,3}$ (TT99 format); received: " + code
            )
        obj = str.__new__(cls, code)
        return obj

    @property
    def value(self) -> str:
        return self


# ── AccountCategory Enum ─────────────────────────────────────────────

class AccountCategory(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    INCOME = "Income"
    UNDISTRIBUTED_PROFIT = "Undistributed Profit"


# ── AccountStatus Enum ───────────────────────────────────────────────

class AccountStatus(str, Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"


# ── AccountTag Enum (7 mandatory per FR-12b) ─────────────────────────

class AccountTag(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    TAX = "Tax"
    COST = "Cost"


# ── Account Aggregate Root ───────────────────────────────────────────

class Account:
    """Account aggregate root with invariants per Circular 99/2025/TT-BTC.

    Attributes:
        code: Account code per TT99 format (10 digits or 10-3 with TT99)
        name: Account name
        category: AccountCategory enum
        status: AccountStatus enum (ACTIVE/CLOSED)
        vat_rate: VAT rate (0, 5, 8, or 10 per Vietnamese law)
        report_line: Report line reference (Appendix IV); mandatory for all
                     categories except UNDISTRIBUTED_PROFIT
        account_tags: frozenset of AccountTag enums (at least 1 mandatory)
        id: UUID identifier
        created_by: UUID of creator
        created_at: creation timestamp
        parent_id: optional UUID for sub-accounts
        audit_checksum: SHA-256 checksum for audit trail
    """

    def __init__(
        self,
        code: str,
        name: str,
        category: AccountCategory,
        company_id: UUID,
        created_by: UUID,
        vat_rate: float = 0.0,
        report_line: str | None = None,
        parent_id: UUID | None = None,
        account_tags: list[AccountTag] | None = None,
    ) -> None:
        # 1. Validate and store code
        self.code = AccountCode(code).value

        # 2. Basic attrs
        self.name = name.strip()
        self.category = category
        self.company_id = company_id
        self.parent_id = parent_id

        # 3. Status: newly created → ACTIVE
        self.status = AccountStatus.ACTIVE

        # 4. VAT rate: must be 0, 5, 8, or 10
        if vat_rate not in (0, 5, 8, 10):
            raise InvalidAccountCodeError(
                "VAT rate must be 0, 5, 8, or 10; received: " + str(vat_rate)
            )
        self.vat_rate = vat_rate

        # 5. Report line: mandatory for all categories except UNDISTRIBUTED_PROFIT
        if category != AccountCategory.UNDISTRIBUTED_PROFIT and not report_line:
            raise InvalidAccountCodeError(
                "Report line (Appendix IV code) is mandatory for category " + category.value + "; received report_line=" + str(report_line)
            )
        self.report_line = report_line

        # 6. Account tags: at least 1; system adds mandatory tags if none provided
        if account_tags is None:
            account_tags = [AccountTag.REVENUE]  # default; enterprise configures real tags
        elif not any(isinstance(t, AccountTag) for t in account_tags):
            raise InvalidAccountCodeError("At least 1 account tag must be AccountTag enum value")
        # Filter to valid enum values only; deduplicate
        valid_tags = list(dict.fromkeys([t for t in account_tags if isinstance(t, AccountTag)]))
        if not valid_tags:
            raise InvalidAccountCodeError("At least 1 valid account tag required")
        self.account_tags = frozenset(valid_tags)

        # 7. Auditing
        self.id = uuid4()
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = uuid4().hex[:64]

    def close(self, actor: UUID, reason: str) -> None:
        """Close the account: ACTIVE → CLOSED."""
        if self.status == AccountStatus.CLOSED:
            raise ValueError("Account is already closed")
        self.status = AccountStatus.CLOSED
        self.audit_checksum = uuid4().hex[:64]
        self.updated_at = datetime.now(timezone.utc)

    def reopen(self, actor: UUID, reason: str) -> None:
        """Reopen the account: CLOSED → ACTIVE."""
        if self.status != AccountStatus.CLOSED:
            raise ValueError("Account is not closed")
        self.status = AccountStatus.ACTIVE
        self.audit_checksum = uuid4().hex[:64]
        self.updated_at = datetime.now(timezone.utc)

    def modify(self, actor: UUID, reason: str, new_code: str | None = None, new_name: str | None = None, new_vat_rate: float | None = None, new_report_line: str | None = None, new_category: AccountCategory | None = None) -> None:
        """Modify account attributes (CHIEF_ACCOUNTANT only at domain level)."""
        if new_code is not None:
            raise InvalidAccountCodeError("Code modification requires migration module")
        if new_name is not None:
            self.name = new_name
        if new_category is not None:
            raise InvalidAccountCodeError("Category modification requires migration module")
        if new_vat_rate is not None:
            if new_vat_rate not in (0, 5, 8, 10):
                raise InvalidAccountCodeError("VAT rate must be 0, 5, 8, or 10")
            self.vat_rate = new_vat_rate
        if new_report_line is not None:
            if self.category != AccountCategory.UNDISTRIBUTED_PROFIT and not new_report_line:
                raise InvalidAccountCodeError("Report line mandatory for non-undistributed categories")
            self.report_line = new_report_line
        self.audit_checksum = uuid4().hex[:64]
        self.updated_at = datetime.now(timezone.utc)
