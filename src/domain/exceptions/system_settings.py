"""System settings domain exceptions."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.base import FlagType, FlagScope, FlagCategory
from src.domain.exceptions import DomainException


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


@dataclass
class FlagDefinition:
    """Metadata for a system flag."""
    name: str
    flag_type: FlagType
    flag_scope: FlagScope
    category: FlagCategory
    requires_2nd_approval: bool = False
    description: str = ""
    legal_basis: str | None = None