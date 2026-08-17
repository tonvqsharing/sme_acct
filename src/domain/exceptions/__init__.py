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
