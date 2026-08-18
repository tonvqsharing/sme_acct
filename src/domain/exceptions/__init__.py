"""Domain exceptions."""

from __future__ import annotations


class DomainException(Exception):
    """Base for all domain-level errors."""


class NotFoundError(DomainException):
    """Entity not found."""


class AlreadyExistsError(DomainException):
    """Duplicate code / identifier."""


class InvalidVoucher(DomainException):
    """Voucher does not balance or status is wrong."""


class InvalidInvoice(DomainException):
    """Invoice integrity error."""


class AccountingPeriodLockedError(DomainException):
    """Operation blocked by closed/locked accounting period."""


class CompanyValidationError(DomainException):
    """Company data validation failure."""


class InvalidCompanyTypeError(DomainException):
    """Company type enum mismatch."""


class DuplicateMSTError(DomainException):
    """MST already registered in system."""


class CompanyNotFoundError(DomainException):
    """Company record not found."""


class CompanyLockedError(DomainException):
    """Company is suspended or dissolved; operation blocked."""


class SystemSettingsError(DomainException):
    """Base for all system settings errors."""


class FlagLockedError(SystemSettingsError):
    """Attempt to modify a LAW-flagged value."""


class ConfigVersionConflict(SystemSettingsError):
    """Config version mismatch (optimistic lock failure)."""


class InvalidVATRateError(SystemSettingsError):
    """VAT rate value fails validation."""


class InvalidCAListError(SystemSettingsError):
    """CA list entries don't match required pattern."""


class InvalidRegimeError(SystemSettingsError):
    """Accounting regime value is invalid for the company type."""


class CurrencyError(DomainException):
    """Base for all currencies & exchange rates errors."""


class InvalidCurrencyError(CurrencyError):
    """Currency code fails ISO 4217 format validation (^[A-Z]{3}$)."""


class CurrencyNotFoundError(CurrencyError):
    """Currency does not exist or is inactive."""


class RateNotFoundError(CurrencyError):
    """No applicable exchange rate found for (currency, date, type)."""


class InvalidRateError(CurrencyError):
    """Rate value fails invariants (must be > 0)."""


class RateLockedError(CurrencyError):
    """Rate referenced by a posted transaction; cannot change."""


class RevaluationError(CurrencyError):
    """Revaluation run violates state machine or balance rule."""


class PeriodLockedError(CurrencyError):
    """Revaluation blocked: accounting period is locked."""


class FXImportError(CurrencyError):
    """CSV rate import failed validation."""


class FiscalYearError(DomainException):
    """Base for all fiscal year / accounting period errors."""


class InvalidFiscalYearError(FiscalYearError):
    """Fiscal year violates Luật 88/2015 Đ12 (not quarter-aligned, bad length)."""


class FiscalYearExistsError(FiscalYearError):
    """Duplicate year_code for the same company."""


class PeriodTransitionError(FiscalYearError):
    """Illegal accounting-period state transition (e.g. YEAR_CLOSED → OPEN)."""


class PeriodNotClosableError(FiscalYearError):
    """Period cannot be closed (open drafts / prerequisites missing)."""


class YearEndPreconditionsError(FiscalYearError):
    """Year-end close blocked: periods not all locked / unposted entries."""


class SelfApprovalError(FiscalYearError):
    """SOD violation: requester == approver on lock/reopen."""
