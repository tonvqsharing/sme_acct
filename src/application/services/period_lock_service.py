"""Period lock service for accounting period enforcement.

Handles fiscal year / accounting period locking per Vietnamese accounting law.
Integrates with CompanyService.validate_active_for_transaction() for
company status checks.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.application.services.company_service import CompanyService
from src.domain.entities.company import CompanyStatus
from src.domain.exceptions import CompanyLockedError, NotFoundError


class PeriodLockService:
    """Enforces accounting period lock rules.

    Period lock prevents posting new entries in a closed/frozen accounting
    period. Integrated with Company.validate_active_for_transaction() for
    company status checks.
    """

    # Period lock key format (can be backed by Redis in production)
    PERIOD_LOCK_KEY = "period_lock:{company_id}:{period}"

    # Fiscal year close key format
    FYEAR_CLOSE_KEY = "fyear_closed:{company_id}:{fyear}"

    def __init__(self, company_service: CompanyService) -> None:
        self._company_service = company_service

    # ── Public API ──────────────────────────────────────────────────────────

    def is_locked(self, company_id: UUID, period: str) -> bool:
        """Returns True if period is LOCKED or FYEAR_CLOSED.

        Args:
            company_id: Target company.
            period: Period string (e.g. "1" for January, or "FY2024").

        Returns:
            True if the period is locked (cannot post entries).
        """
        # First check company status (already suspended/dissolved)
        try:
            self._company_service.validate_active_for_transaction(company_id)
        except CompanyLockedError:
            return True  # Company itself is locked

        # TODO: In production, check DB period_locks table
        # For v1, we check if a period lock exists via the repo
        # For now, this is a stub - actual DB triggers handled by migrations
        return False

    def lock_period(self, company_id: UUID, period: str, actor: UUID) -> None:
        """Lock an accounting period.

        Requires ACCOUNTANT or ADMIN role (enforced by presentation layer).

        Args:
            company_id: Target company.
            period: Period to lock (e.g. "1" for January).
            actor: User performing the lock.
        """
        # Company must be active to lock periods
        self._company_service.validate_active_for_transaction(company_id)
        # TODO: In production, write to period_locks table
        # For v1, we just record the intent

    def close_fiscal_year(self, company_id: UUID, fyear: int, actor: UUID) -> None:
        """Close a fiscal year (irreversible).

        Requires CHIEF_ACCOUNTANT role (enforced by presentation layer).

        Args:
            company_id: Target company.
            fyear: Fiscal year to close (e.g. 2024).
            actor: User performing the close.
        """
        # Company must be active to close FY
        self._company_service.validate_active_for_transaction(company_id)
        # TODO: In production, write to period_locks table
        # For v1, we just record the intent

    def validate_before_entry(self, company_id: UUID, entry_date: date) -> None:
        """Block new transactions for locked periods.

        Called by InvoiceService and VoucherService before accepting entries.

        Args:
            company_id: Target company.
            entry_date: Date of the entry being posted.

        Raises:
            CompanyLockedError: If period is locked or company is inactive.
        """
        # First check company status (SUSPENDED/DISSOLVED)
        self._company_service.validate_active_for_transaction(company_id)

        # TODO: In production, check DB period_locks for the given date
        # For v1, we delegate to the company's fiscal year helper
        # which derives the fiscal year/period from the entry date
        company = self._company_service.get_company(company_id)
        fym = company.fiscal_year_start_month
        fyd = company.fiscal_year_start_day

        # Derive fiscal year and period from entry date
        if entry_date.month > fym or (entry_date.month == fym and entry_date.day >= fyd):
            accounting_period = entry_date.month - fym + 1
        else:
            accounting_period = entry_date.month + 12 - fym + 1

        # For v1, we check if the derived period would be locked
        # In production, this would query the period_locks table
        # For now, always allow (stub implementation)
        # TODO: Query DB: SELECT * FROM period_locks 
        #       WHERE company_id = ? AND fiscal_year = ? AND period = ?