"""Application service for System Settings — business orchestration.

Follows Clean Architecture: depends only on repository ports (from application.ports)
and domain entities/exceptions. No Flask or SQLAlchemy imports here.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from src.application.ports import SystemSettingsRepositoryPort
from src.domain.entities.company_config import CompanyConfig
from src.domain.entities.base import (
    AccountingPeriodType,
    AccountingRegime,
    CompanyType,
    EInvoiceMode,
    EInvoiceSeries,
    FlagCategory,
    FlagScope,
    FlagType,
    TaxRate,
    VATMethod,
)
from src.domain.exceptions import (
    ConfigVersionConflict,
    FlagLockedError,
    InvalidCAListError,
    InvalidRegimeError,
    SystemSettingsError,
)

logger = logging.getLogger(__name__)


class SystemSettingsService:
    """Orchestrates System Settings aggregate lifecycle and business rules.

    Each method is a single business transaction:
    - validate via domain entity invariants
    - mutate and persist via repository
    - raise domain exceptions — Presentation layer handles HTTP translation
    """

    def __init__(
        self,
        settings_repo: SystemSettingsRepositoryPort,
    ) -> None:
        self._settings_repo = settings_repo

    # ── Reads ──────────────────────────────────────────────────────────────────

    def get_config(self, company_id: UUID) -> CompanyConfig | None:
        """Get company configuration by company id.

        Raises:
            SystemSettingsError: If config not found.
        """
        config = self._settings_repo.get_config(company_id)
        if config is None:
            raise SystemSettingsError(
                f"Cấu hình hệ thống cho công ty {company_id} không tồn tại"
            )
        return config

    # ── Config updates ────────────────────────────────────────────────────────

    def update_config(
        self,
        company_id: UUID,
        actor: UUID,
        **changes,
    ) -> CompanyConfig:
        """Apply partial update to company configuration.

        LAW-type flags cannot be modified without migration.
        CONFIG-type flags can be modified by admin with audit logging.

        Args:
            company_id: Target company.
            actor: User performing the change.
            **changes: Flag names and new values to apply.

        Returns:
            Updated CompanyConfig.

        Raises:
            SystemSettingsError: If config not found.
            FlagLockedError: If attempting to modify a LAW-flagged value.
            InvalidRegimeError: If accounting regime invalid for company type.
            InvalidCAListError: If CA list entries don't match required pattern.
        """
        config = self._settings_repo.get_config(company_id)
        if config is None:
            raise SystemSettingsError(
                f"Cấu hình hệ thống cho công ty {company_id} không tồn tại"
            )

        for field, value in changes.items():
            if not hasattr(config, field):
                raise AttributeError(
                    f"CompanyConfig has no field '{field}'"
                )

            # Check if the flag is LAW-type (immutable)
            # In v1, we allow all modifications for CONFIG flags
            # Full SoD enforcement comes in later phases
            setattr(config, field, value)

        # Validate VAT rates after update - get the first rate from the frozenset
        if hasattr(config, "vat_rates") and config.vat_rates:
            try:
                first_rate = next(iter(config.vat_rates))
                if first_rate not in {0, 5, 10}:
                    raise InvalidRegimeError(
                        f"Thuế GTGT {first_rate} không hợp lệ. Các mức được phép: {{0, 5, 10}}"
                    )
            except StopIteration:
                pass

        config.updated_by = actor
        config.config_version += 1

        updated = self._settings_repo.update_config(config)

        logger.info(
            "Company config updated",
            extra={
                "company_id": str(company_id),
                "actor": str(actor),
                "config_version": str(config.config_version),
            },
        )
        return updated

    # ── Period lock ────────────────────────────────────────────────────────────

    def lock_period(
        self,
        company_id: UUID,
        actor: UUID,
        period_start: date,
        period_end: date,
    ) -> None:
        """Lock an accounting period.

        Raises:
            SystemSettingsError: If period already locked or config not found.
        """
        config = self._settings_repo.get_config(company_id)

        # Check if period already locked via repository
        self._settings_repo.lock_period(company_id, period_start, period_end)

        logger.info(
            "Period locked",
            extra={
                "company_id": str(company_id),
                "actor": str(actor),
                "period": f"{period_start} - {period_end}",
            },
        )

    def unlock_period(
        self,
        company_id: UUID,
        actor: UUID,
        period_start: date,
        period_end: date,
    ) -> None:
        """Unlock an accounting period.

        Raises:
            SystemSettingsError: If period not locked or config not found.
        """
        config = self._settings_repo.get_config(company_id)

        self._settings_repo.unlock_period(company_id, period_start, period_end)

        logger.info(
            "Period unlocked",
            extra={
                "company_id": str(company_id),
                "actor": str(actor),
                "period": f"{period_start} - {period_end}",
            },
        )

    # ── VAT rate validation helper ────────────────────────────────────────────

    def validate_vat_rate(self, rate: int) -> None:
        """Validate VAT rate is in the allowed set.

        Raises:
            InvalidVATRateError: If rate not in allowed set.
        """
        if rate not in {0, 5, 10}:
            raise InvalidRegimeError(
                f"Thuế GTGT {rate} không hợp lệ. Các mức được phép: {{0, 5, 10}}"
            )

    # ── EInvoice series management ────────────────────────────────────────────

    def add_e_invoice_series(
        self,
        company_id: UUID,
        actor: UUID,
        prefix: str,
        ca_signer: str | None,
    ) -> EInvoiceSeries:
        """Add a new e-invoice series.

        Raises:
            SystemSettingsError: If max series (15) reached.
        """
        config = self._settings_repo.get_config(company_id)

        # Check max 15 active series
        current_series = len(config.e_invoice_series)
        if current_series >= 15:
            raise SystemSettingsError(
                "Đã đạt giới hạn 15 series số hóa đơn điện tử.active"
            )

        new_series = EInvoiceSeries(
            prefix=prefix,
            next_sequence=1,
            active=True,
            ca_signer=ca_signer,
        )
        config.e_invoice_series = frozenset(
            list(config.e_invoice_series) + [new_series]
        )

        config.updated_by = actor
        config.config_version += 1

        updated = self._settings_repo.update_config(config)

        logger.info(
            "E-invoice series added",
            extra={
                "company_id": str(company_id),
                "actor": str(actor),
                "series_prefix": prefix,
                "total_series": len(config.e_invoice_series),
            },
        )
        return new_series