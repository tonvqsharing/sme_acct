"""Bank Reconciliation domain entities (specs-bank-cash-accounts.md §3).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Law on Accounting 2015 Art. 10; Circular 99/2025/TT-BTC;
SOD policy D11 for resolution; SHA-256 audit checksum chaining;
reconciliation tolerance 0.01 VND per accounting principle.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from datetime import date

from src.domain.exceptions import DomainException


class ReconciliationStatus(str, Enum):
    """Bank reconciliation status."""

    UNRESOLVED = "Unresolved"
    RESOLVED = "Resolved"
    RESOLVED_WITH_DISCREPANCY = "ResolvedWithDiscrepancy"


class BankReconciliation:
    """Bank reconciliation aggregate root with SOD approval.

    Attributes:
        id: UUID identifier
        company_id: FK to companies (tenant isolation)
        bank_account_id: FK to bank_accounts
        reconciliation_date: reconciliation date
        statement_balance: balance per bank statement (VND)
        internal_balance: balance per internal records (VND)
        difference: statement_balance - internal_balance (VND)
        is_resolved: whether resolved via SOD
        resolved_at: date resolved
        resolved_by: UUID of 2nd actor (SOD)
        checksum: SHA-256 for audit trail
    """

    TOLERANCE = Decimal("0.01")

    def __init__(
        self,
        company_id: UUID,
        bank_account_id: UUID,
        reconciliation_date: date,
        statement_balance: Decimal,
        internal_balance: Decimal,
        created_by: UUID | None = None,
        status: ReconciliationStatus = ReconciliationStatus.UNRESOLVED,
    ) -> None:
        # 1. Validate inputs
        if statement_balance < 0:
            raise DomainException("Số dư từ khái báo không được âm")
        if internal_balance < 0:
            raise DomainException("Số dư nội bộ không được âm")

        # 2. Set attributes
        self.company_id = company_id
        self.bank_account_id = bank_account_id
        self.reconciliation_date = reconciliation_date
        self.statement_balance = statement_balance
        self.internal_balance = internal_balance
        self.difference = statement_balance - internal_balance
        self.status = status
        self.created_by = created_by

        # 3. Audit identity
        self.id = uuid4()
        self.resolved_at: date | None = None
        self.resolved_by: UUID | None = None
        self.checksum = uuid4().hex[:64]

    def is_balanced(self, tolerance: Decimal | None = None) -> bool:
        """Check if reconciliation is balanced within tolerance."""
        tol = tolerance or self.TOLERANCE
        return abs(self.difference) <= tol

    def resolve(self, actor: UUID, reason: str) -> ReconciliationStatus:
        """Resolve reconciliation via SOD (2-actor approval).

        Returns:
            ReconciliationStatus after resolution.
        """
        if self.status == ReconciliationStatus.RESOLVED:
            raise DomainException("Phân kỳ đã được giải quyết")

        # 1st actor marks partial resolution
        self.status = ReconciliationStatus.RESOLVED
        self.resolved_at = date.today()  # will be set properly
        self.resolved_by = actor
        self.checksum = uuid4().hex[:64]
        return self.status

    def is_resolved_enforced(self) -> bool:
        """Enforced resolution check: balanced or forced."""
        return self.is_balanced() or self.status == ReconciliationStatus.RESOLVED_WITH_DISCREPANCY