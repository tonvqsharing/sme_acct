"""System settings / tax config domain. Pure Python. Per specs-tax-engine §2."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TaxRate(Enum):
    """Thuế suất theo quy định Việt Nam (percent integers).

    VAT_8 is a TEMPORARY reduced rate per NQ 204/2025/QH15 +
    NĐ 174/2025/NĐ-CP, eff 01/07/2025 → 31/12/2026 (invoice prints
    "8%"). Reverts to Luật GTGT 2024 rates after that date — revisit
    this enum when the decree expires.
    Exclusions while active: viễn thông, tài chính/NH/CK/bảo hiểm,
    BĐS, kim loại & đúc sẵn, khai khoáng (trừ than), TTĐB (trừ xăng).
    Source: gdt.gov.vn reform page + thuvienphapluat.vn, verified
    2026-08-24.
    """

    VAT_0 = 0
    VAT_5 = 5
    VAT_8 = 8
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
    legal_reviewed_at: datetime | None = None
    legal_reviewed_by: UUID | None = None

    # ── CONFIG flags (changeable) ────────────────────────────────────────
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    vat_settlement_cycle: str = "monthly"  # monthly | quarterly
    decimal_places: int = 2
    default_currency: str = "VND"
    cost_center_required: bool = False

    def with_series(self, series: EInvoiceSeries, actor: UUID) -> CompanyConfig:
        """Immutable update — returns new config, bumps version."""
        return replace(
            self,
            e_invoice_series=frozenset({*self.e_invoice_series, series}),
            updated_by=actor,
            config_version=self.config_version + 1,
        )

    def with_flag_update(self, flag_name: str, value: Any, actor: UUID) -> CompanyConfig:
        """Update a CONFIG-type flag. Returns new config, bumps version."""
        if not hasattr(self, flag_name):
            raise ValueError(f"Unknown flag: {flag_name}")
        return replace(
            self,
            **{flag_name: value},
            updated_by=actor,
            config_version=self.config_version + 1,
        )

    def with_legal_review(self, actor: UUID, reviewed_at: Any) -> CompanyConfig:
        """Stamp legal review. Returns new config, bumps version."""
        return replace(
            self,
            legal_reviewed_by=actor,
            legal_reviewed_at=reviewed_at,
            updated_by=actor,
            config_version=self.config_version + 1,
        )
