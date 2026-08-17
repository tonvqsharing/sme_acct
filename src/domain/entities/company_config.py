"""Company configuration entity — System Settings module.

Domain aggregate holding all system-level settings for a single company.
Exactly one per company, scoped by company_id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.domain.entities.base import (
    AccountingPeriodType,
    AccountingRegime,
    CompanyType,
    EInvoiceSeries,
    FlagCategory,
    FlagScope,
    FlagType,
    TaxRate,
    VATMethod,
    EInvoiceMode,
)
from src.domain.exceptions import SystemSettingsError
from src.domain.value_objects import TaxId  # type: ignore


@dataclass
class CompanyConfig:
    """Domain aggregate holding all system-level settings for a single company.

    Exactly one per company. Mix of LAW-type (immutable legal constants)
    and CONFIG-type (admin-changeable with audit log + 2nd approval).
    """

    company_id: UUID  # FK to Company (or root if no Company entity yet)

    # ── Legal constants (LAW type — cannot be changed without migration) ──
    accounting_period_type: AccountingPeriodType   # CALENDAR | FISCAL_15 | FISCAL_APR
    accounting_regime: AccountingRegime           # TT200 | TT99 | TT58_MICRO | TT133
    chart_of_accounts_type: FlagCategory          # COA_200 | COA_99 | COA_ENTERPRISE
    tax_id_pattern: str                           # r"^\d{10}(-\d{3})?$" (hardcoded)
    account_code_pattern: str                     # r"^[1-9]\d{2}$|^[1-9]\d{3}$" (hardcoded)
    vat_rates: frozenset[int]                     # {0, 5, 10} ← system managed
    minimum_retention_years: int                  # ≥10; ties to company type
    data_deletable: bool                          # False after fiscal year close

    # ── Config flags (CONFIG type — changeable with admin role + audit log) ──
    fiscal_year_start_month: int                  # 1-12; default 1 (Jan)
    fiscal_year_start_day: int                    # 1-31; default 1
    vat_settlement_cycle: str                     # MONTHLY | QUARTERLY
    vat_method: VATMethod                         # DEDUCTION | OUTPUT_ONLY
    e_invoice_mode: EInvoiceMode                  # SOFTWARE_CERT | CA_SIGNED
    ca_list: frozenset[str]                       # List of GDT-approved CA identifiers
    e_invoice_series: frozenset[EInvoiceSeries]   # Max 15 active; each has prefix, next_seq
    decimal_places: int                           # 0 | 2
    default_currency: str                         # "VND" default
    cost_center_required: bool                    # False default
    multi_level_cost_centers: bool                # False default
    default_cost_formula: str                     # "FIFO" (TT200 standard)
    data_retention_years: int                     # ≥10 per decree

    # ── Audit-only metadata (never user-editable) ──
    created_at: date
    created_by: UUID
    updated_at: date
    updated_by: UUID
    config_version: int                           # optimistic-lock; increments per change
    legal_reviewed_at: date | None                # When chief accountant approved
    legal_reviewed_by: UUID | None

    # ── Business rules ──────────────────────────────────────────────────

    def validate_vat_rate(self, rate: int) -> None:
        """Validate VAT rate is in the allowed set."""
        if rate not in self.vat_rates:
            raise SystemSettingsError(
                f"Thuế GTGT {rate} không hợp lệ. Các mức được phép: {self.vat_rates}"
            )


@dataclass
class CompanyConfigChange:
    """Record of a CompanyConfig change for audit trail."""
    config_version: int
    flag_name: str
    flag_type: FlagType
    before_value: str | None
    after_value: str | None
    actor: UUID
    changed_at: date
    legal_reviewed: bool = False
    legal_basis: str | None = None