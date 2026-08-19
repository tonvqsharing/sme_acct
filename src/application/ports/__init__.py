"""Application layer: use cases coordinate domain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from src.domain.entities.company import Company
from src.domain.entities.contact import Partner
from src.domain.entities.currency import Currency, ExchangeRate, FXDifference, RevaluationRun
from src.domain.entities.base import RateType
from src.domain.entities.fiscal_year import (
    AccountingPeriod,
    FiscalYear,
    PeriodLockEvent,
)
from src.domain.entities.invoice import Invoice, InvoiceItem, InvoiceStatus, InvoiceType
from src.domain.entities.voucher import DocumentType, Voucher, VoucherLine, VoucherStatus
from src.domain.entities.company_config import CompanyConfig


class CompanyRepositoryPort(ABC):
    @abstractmethod
    def create(self, company: Company) -> Company:
        pass

    @abstractmethod
    def update(self, company: Company) -> Company:
        """Persist changes to an existing company (matched by MST)."""
        pass

    @abstractmethod
    def get_by_id(self, company_id: UUID) -> Company | None:
        pass

    @abstractmethod
    def get_by_mst(self, mst: str) -> Company | None:
        pass

    @abstractmethod
    def get_active(self) -> Company | None:
        pass

    @abstractmethod
    def list_active(self, page: int = 1, page_size: int = 20) -> list[Company]:
        pass


class PartnerRepositoryPort(ABC):
    @abstractmethod
    def create(self, partner: Partner) -> Partner:
        pass

    @abstractmethod
    def get_by_id(self, partner_id: UUID) -> Partner | None:
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> Partner | None:
        pass

    @abstractmethod
    def list_active(self, page: int = 1, page_size: int = 20) -> list[Partner]:
        pass


class InvoiceRepositoryPort(ABC):
    @abstractmethod
    def create(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    def get_by_id(self, invoice_id: UUID) -> Invoice | None:
        pass

    @abstractmethod
    def get_by_serial_number(self, serial: str, invoice_number: str) -> Invoice | None:
        pass

    @abstractmethod
    def list_by_partner(
        self,
        partner_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Invoice]:
        pass


class VoucherRepositoryPort(ABC):
    @abstractmethod
    def create(self, voucher: Voucher) -> Voucher:
        pass

    @abstractmethod
    def get_by_id(self, voucher_id: UUID) -> Voucher | None:
        pass

    @abstractmethod
    def get_by_number(self, voucher_number: str) -> Voucher | None:
        pass

    @abstractmethod
    def lock(self, voucher_id: UUID) -> Voucher:
        pass


class AccountChartRepositoryPort(ABC):
    @abstractmethod
    def get_balance(self, account_code: str, from_date: date, to_date: date) -> dict:
        pass


class SystemSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_config(self, company_id: UUID) -> CompanyConfig | None:
        pass

    @abstractmethod
    def update_config(self, config: CompanyConfig) -> CompanyConfig:
        pass

    @abstractmethod
    def lock_period(self, company_id: UUID, period_start: date, period_end: date) -> None:
        pass

    @abstractmethod
    def unlock_period(self, company_id: UUID, period_start: date, period_end: date) -> None:
        pass

    @abstractmethod
    def audit_log(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        field_name: str | None,
        before_value: str | None,
        after_value: str | None,
    ) -> None:
        pass


class UserRepositoryPort(ABC):
    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def update(self, user: User, actor: UUID) -> User:
        pass

    @abstractmethod
    def deactivate(self, user_id: UUID, actor: UUID) -> User:
        pass

    @abstractmethod
    def activate(self, user_id: UUID, actor: UUID) -> User:
        pass

    @abstractmethod
    def list_active(self) -> list[User]:
        pass

    @abstractmethod
    def list_by_role(self, role: UserRole) -> list[User]:
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        pass



class AccountRepositoryPort(ABC):
    '''Port for Chart of Accounts master data.'''

    @abstractmethod
    def create(self, account: Account) -> Account:
        pass

    @abstractmethod
    def get_by_id(self, account_id: UUID) -> Account | None:
        pass

    @abstractmethod
    def get_by_code(self, code: str, company_id: UUID) -> Account | None:
        pass

    @abstractmethod
    def update(self, account: Account) -> Account:
        pass

    @abstractmethod
    def list_by_company(
        self,
        company_id: UUID,
        *,
        category: AccountCategory | None = None,
        status: AccountStatus | None = None,
        tag: AccountTag | None = None,
        VAT_rate: float | None = None,
    ) -> list[Account]:
        pass

    @abstractmethod
    def soft_delete(self, account_id: UUID, actor: UUID, reason: str) -> Account:
        '''Soft-delete: set status=CLOSED; do NOT row-delete per Law on Accounting 10-year retention.'''


class AccountCategoryRepositoryPort(ABC):
    '''Port for AccountCategory system categories.'''

    @abstractmethod
    def get_system_categories(self) -> list[AccountCategory]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> AccountCategory | None:
        pass


class AccountTagRepositoryPort(ABC):
    '''Port for AccountTag master data (7 mandatory tags per FR-12b).'''

    @abstractmethod
    def list_mandatory_tags(self) -> list[AccountTag]:
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> AccountTag | None:
        pass

    @abstractmethod
    def create(self, tag: AccountTag) -> AccountTag:
        pass

    @abstractmethod
    def update(self, tag: AccountTag) -> AccountTag:
        pass


class AuditLogRepositoryPort(ABC):
    """Port for audit log persistence operations.

    Abstract interface separating audit log storage concerns from
    application service logic. Implementations handle INSERT-only
    write paths with immutability enforcement at the database level.
    """

    @abstractmethod
    def create(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        field_name: str | None,
        before_value: str | None,
        after_value: str | None,
        actor_id: UUID,
    ) -> object:
        """Create a new audit log record.

        INSERT-only operation; no UPDATE/DELETE permitted on core audit table.
        Returns the created record entity for service-layer response mapping.
        """

    @abstractmethod
    def get_filtered(
        self,
        entity_type: str | None,
        entity_id: UUID | None,
        action: str | None,
        field_name: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        actor_id: UUID | None,
        page: int,
        page_size: int,
    ) -> dict:
        """Query audit records with filtering and pagination.

        Returns paged result dict with items and total_count.
        """

    @abstractmethod
    def get_all_ordered(self) -> list:
        """Get all audit records ordered by changed_at (for integrity verification)."""
        pass


class CurrencyRepositoryPort(ABC):
    """Port for currency master data (specs-currencies.md §2.1)."""

    @abstractmethod
    def get(self, code: str) -> Currency | None:
        pass

    @abstractmethod
    def list_active(self) -> list[Currency]:
        pass

    @abstractmethod
    def save(self, currency: Currency) -> Currency:
        pass

    @abstractmethod
    def exists(self, code: str) -> bool:
        pass


class ExchangeRateRepositoryPort(ABC):
    """Port for exchange rate history (specs §2.2, D2/D3: append-only)."""

    @abstractmethod
    def create(self, rate: ExchangeRate) -> ExchangeRate:
        """Insert a new rate row. No in-place update (D3)."""

    @abstractmethod
    def get_latest(
        self, currency_code: str, rate_type: RateType, rate_date: date
    ) -> ExchangeRate | None:
        """Last available rate with (currency, type) on or before rate_date."""

    @abstractmethod
    def list_history(
        self,
        currency_code: str | None,
        rate_type: RateType | None,
        from_date: date | None,
        to_date: date | None,
    ) -> list[ExchangeRate]:
        pass

    @abstractmethod
    def rate_is_referenced(self, rate_id: UUID) -> bool:
        """True when a posted transaction references the rate (D3 lock)."""


class RevaluationRepositoryPort(ABC):
    """Port for revaluation runs (specs §2.5, D7/D8)."""

    @abstractmethod
    def create_run(self, run: RevaluationRun) -> RevaluationRun:
        pass

    @abstractmethod
    def save_run(self, run: RevaluationRun) -> RevaluationRun:
        """Persist state changes (approve/post/reverse)."""

    @abstractmethod
    def get_run(self, run_id: UUID) -> RevaluationRun | None:
        pass

    @abstractmethod
    def get_posted_run(
        self, company_id: UUID, period_start: date, period_end: date
    ) -> RevaluationRun | None:
        """Most recent POSTED run for (company, period) — idempotent re-run (D7)."""

    @abstractmethod
    def period_is_locked(self, company_id: UUID, period_start: date, period_end: date) -> bool:
        """Check period_locks table (D8)."""

    @abstractmethod
    def list_fx_differences(
        self, company_id: UUID, period_start: date, period_end: date
    ) -> list[FXDifference]:
        pass


class FiscalYearRepositoryPort(ABC):
    """Port for fiscal years (specs §4.1)."""

    @abstractmethod
    def save(self, fiscal_year: FiscalYear) -> FiscalYear:
        pass

    @abstractmethod
    def get_active(self, company_id: UUID, entry_date: date) -> FiscalYear | None:
        """FY whose range contains entry_date, with periods loaded."""
        pass

    @abstractmethod
    def get_by_id(self, fiscal_year_id: UUID) -> FiscalYear | None:
        pass

    @abstractmethod
    def list_by_company(self, company_id: UUID) -> list[FiscalYear]:
        pass


class PeriodLockRepositoryPort(ABC):
    """Port for period lock state + append-only lock events (R-08).

    Adapter dual-writes legacy period_locks rows (currencies D8 path)
    and the new accounting_periods.status truth.
    """

    @abstractmethod
    def get_period(self, period_id: UUID) -> AccountingPeriod | None:
        pass

    @abstractmethod
    def find_period(self, company_id: UUID, entry_date: date) -> AccountingPeriod | None:
        pass

    @abstractmethod
    def is_locked(self, company_id: UUID, entry_date: date) -> bool:
        pass

    @abstractmethod
    def lock(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        pass

    @abstractmethod
    def reopen(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        pass

    @abstractmethod
    def history(self, period_id: UUID) -> list[PeriodLockEvent]:
        pass
