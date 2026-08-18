"""CurrencyService — currency master data + rate maintenance.

Clean Architecture: depends only on repository ports + domain entities.
Follows CompanyService pattern. Docs: specs-currencies.md §2.1, rules D1/D4.
"""

from __future__ import annotations

import logging
from uuid import UUID

from src.application.ports import CurrencyRepositoryPort
from src.domain.entities.currency import Currency
from src.domain.exceptions import (
    CurrencyNotFoundError,
    InvalidCurrencyError,
)

logger = logging.getLogger(__name__)


class CurrencyService:
    """Orchestrates currency master data lifecycle."""

    def __init__(self, currency_repo: CurrencyRepositoryPort) -> None:
        self._currency_repo = currency_repo

    # ── Reads ──────────────────────────────────────────────────────────────

    def list_currencies(self) -> list[Currency]:
        return self._currency_repo.list_active()

    def get_currency(self, code: str) -> Currency:
        currency = self._currency_repo.get(code)
        if currency is None:
            raise CurrencyNotFoundError(f"Tiền tệ '{code}' không tồn tại")
        return currency

    # ── Writes ─────────────────────────────────────────────────────────────

    def create_currency(self, currency: Currency) -> Currency:
        """Create a new currency. Code must be valid ISO 4217 (D1)."""
        if self._currency_repo.exists(currency.code):
            raise InvalidCurrencyError(f"Tiền tệ '{currency.code}' đã tồn tại")
        return self._currency_repo.save(currency)

    def update_currency(self, currency: Currency) -> Currency:
        """Update name/symbol/etc. Code (PK) is identity — create new for new code."""
        existing = self._currency_repo.get(currency.code)
        if existing is None:
            raise CurrencyNotFoundError(f"Tiền tệ '{currency.code}' không tồn tại")
        return self._currency_repo.save(currency)

    def deactivate_currency(self, code: str, actor: UUID) -> Currency:
        """Deactivate a currency. Base currency immutable (D4)."""
        currency = self.get_currency(code)
        if currency.is_base:
            raise InvalidCurrencyError(
                f"Tiền tệ gốc '{code}' không thể vô hiệu hóa (LAW-immutable, D4)"
            )
        deactivated = Currency(
            code=currency.code,
            name=currency.name,
            symbol=currency.symbol,
            decimal_places=currency.decimal_places,
            is_base=currency.is_base,
            is_active=False,
            display_format=currency.display_format,
        )
        return self._currency_repo.save(deactivated)
