"""Port — system settings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.system_settings.domain import CompanyConfig


class SystemSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_config(self, company_id: UUID) -> CompanyConfig: ...
    @abstractmethod
    def update_config(self, cfg: CompanyConfig) -> CompanyConfig: ...


# Canonical lawful VAT fractions — mirrors TaxRate.to_fraction() values.
# Single source of truth; invoice/purchase services default their rate
# gate to this set (brick-boundary-safe: contracts may be imported).
from decimal import Decimal as _D

ALLOWED_VAT_FRACTIONS = frozenset(
    str(_D(str(r.value)) / _D(100))
    for r in __import__("src.bricks.system_settings.domain", fromlist=["TaxRate"]).TaxRate
    if r.value >= 0  # NOT_TAXED(-1) is item-level only
)
