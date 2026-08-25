"""System settings / tax config domain. Pure Python. Per specs-tax-engine §2."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class TaxRate(Enum):
    """Thuế suất theo quy định Việt Nam (percent integers)."""

    VAT_0 = 0
    VAT_5 = 5
    VAT_10 = 10
    NOT_TAXED = -1

    def to_fraction(self) -> Decimal:
        """Bridge to invoice/voucher decimal-fraction world."""
        if self is TaxRate.NOT_TAXED:
            return Decimal(0)
        return Decimal(self.value) / Decimal(100)


class InvalidRegimeError(Exception):
    pass


class FlagLockedError(Exception):
    """LAW-type flags are immutable without a migration."""


@dataclass(frozen=True)
class EInvoiceSeries:
    prefix: str
    next_sequence: int = 1
    active: bool = True
    ca_signer: str | None = None
    id: UUID = field(default_factory=uuid4)


DEFAULT_VAT_RATES = frozenset({0, 5, 10})


@dataclass
class CompanyConfig:
    company_id: UUID
    vat_rates: frozenset[int] = DEFAULT_VAT_RATES
    e_invoice_series: frozenset[EInvoiceSeries] = frozenset()
    config_version: int = 0
    updated_by: UUID | None = None

    def with_series(self, series: EInvoiceSeries, actor: UUID) -> CompanyConfig:
        """Immutable update — returns new config, bumps version."""
        return replace(
            self,
            e_invoice_series=frozenset({*self.e_invoice_series, series}),
            updated_by=actor,
            config_version=self.config_version + 1,
        )
