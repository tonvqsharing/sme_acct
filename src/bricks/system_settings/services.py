"""SystemSettings service — VAT rate validation + e-invoice series SOD."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.bricks.system_settings.domain import (
    CompanyConfig,
    EInvoiceSeries,
    FlagLockedError,
    InvalidRegimeError,
)


class MaxSeriesExceededError(Exception):
    code = "MAX_SERIES_EXCEEDED"


class DuplicateSeriesPrefixError(Exception):
    code = "DUPLICATE_SERIES_PREFIX"


class SodViolationError(Exception):
    code = "SOD_VIOLATION"


LAWFUL_RATES = frozenset({0, 5, 10})
MAX_SERIES = 15


class SystemSettingsService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    # ── VAT rates (LAW-type) ────────────────────────────────────────────
    def validate_vat_rate(self, rate: int) -> None:
        """§3.1: only {0,5,10} are deductible-rate candidates.

        NOT_TAXED(-1) exists as an item-level exemption flag on TaxRate
        but is not a company-configurable deductible rate.
        """
        if rate not in LAWFUL_RATES:
            raise InvalidRegimeError(
                f"Thuế GTGT {rate} không hợp lệ. " f"Các mức được phép: {sorted(LAWFUL_RATES)}"
            )

    def get_config(self, cid: UUID) -> CompanyConfig:
        cfg: CompanyConfig = self._repo.get_config(cid)
        return cfg

    def set_vat_rates(self, cid: UUID, rates: set[int], *, actor: UUID) -> None:
        """R-FLAG: LAW-type — immutable without migration. Always locked."""
        raise FlagLockedError("vat_rates là LAW-type; thay đổi chỉ qua migration có phê duyệt")

    # ── e-invoice series (CONFIG-type, SOD) ─────────────────────────────
    def add_e_invoice_series(
        self,
        company_id: UUID,
        *,
        actor: UUID,
        prefix: str,
        ca_signer: str | None,
        approver: UUID,
    ) -> EInvoiceSeries:
        """§3.1 add_e_invoice_series — max 15, CA signer, 2nd approval.

        Adaptation note: spec's full approval workflow is realized as an
        explicit distinct `approver` argument enforced here (actor ≠
        approver); role authority is enforced at the API layer.
        """
        if approver == actor:
            raise SodViolationError("Cần người phê duyệt khác người thực hiện")
        cfg = self.get_config(company_id)
        if len(cfg.e_invoice_series) >= MAX_SERIES:
            raise MaxSeriesExceededError("Đã đạt giới hạn 15 series hóa đơn điện tử active")
        if any(x.prefix == prefix for x in cfg.e_invoice_series):
            raise DuplicateSeriesPrefixError(f"Prefix {prefix} đã tồn tại")
        new_series = EInvoiceSeries(prefix=prefix, ca_signer=ca_signer)
        updated = cfg.with_series(new_series, actor)
        saved: CompanyConfig = self._repo.update_config(updated)
        assert saved.config_version >= 1
        return new_series
