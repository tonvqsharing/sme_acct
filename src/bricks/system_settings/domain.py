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

# CONFIG-type flags that can be updated via API
CONFIG_FLAGS = frozenset(
    {
        "fiscal_year_start_month",
        "fiscal_year_start_day",
        "vat_settlement_cycle",
        "decimal_places",
        "default_currency",
        "cost_center_required",
    }
)


def _validate_flag_value(flag_name: str, value: Any) -> None:
    """Validate CONFIG flag value at domain boundary."""
    if flag_name == "fiscal_year_start_month":
        if not isinstance(value, int) or not 1 <= value <= 12:
            raise ValueError(f"fiscal_year_start_month must be 1-12, got {value!r}")
    elif flag_name == "fiscal_year_start_day":
        if not isinstance(value, int) or not 1 <= value <= 31:
            raise ValueError(f"fiscal_year_start_day must be 1-31, got {value!r}")
    elif flag_name == "vat_settlement_cycle":
        if value not in ("monthly", "quarterly"):
            raise ValueError(
                f"vat_settlement_cycle must be 'monthly' or 'quarterly', got {value!r}"
            )
    elif flag_name == "decimal_places":
        if value not in (0, 2):
            raise ValueError(f"decimal_places must be 0 or 2, got {value!r}")
    elif flag_name == "default_currency":
        if not isinstance(value, str) or len(value) != 3:
            raise ValueError(f"default_currency must be 3-letter ISO code, got {value!r}")
    elif flag_name == "cost_center_required" and not isinstance(value, bool):
        raise ValueError(f"cost_center_required must be bool, got {value!r}")


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
        if flag_name not in CONFIG_FLAGS:
            raise ValueError(f"Unknown or immutable flag: {flag_name}")
        _validate_flag_value(flag_name, value)
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


@dataclass
class TaxCode:
    """Detailed tax code master beyond TaxRate enum. TT99 3331/1331 detail."""

    company_id: UUID
    code: str  # e.g. VAT-0, VAT-5, VAT-8, VAT-10, KCT, KK
    rate: int  # -1,0,5,8,10
    type: str  # input/output/both
    account_code: str  # 1331/3331
    name: str = ""
    active: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if self.rate not in (-1, 0, 5, 8, 10):
            raise ValueError(f"rate {self.rate} invalid (-1/0/5/8/10)")
        if self.type not in ("input", "output", "both"):
            raise ValueError(f"type {self.type} invalid")
        if not self.account_code.strip():
            raise ValueError("account_code required")
