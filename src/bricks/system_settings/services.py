"""SystemSettings service — VAT rate validation + e-invoice series SOD."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
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


# Base rates per Luật GTGT 2024 + reduced 8% per NQ 204/2025/QH15 /
# NĐ 174/2025/NĐ-CP (eff → 31/12/2026). NOT_TAXED(-1) remains an
# item-level exemption flag, not a configurable deductible rate.
LAWFUL_RATES = frozenset({0, 5, 8, 10})
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


# ═══ VAT declaration engine (specs-vat-declaration.md) ════════════════════


class InvalidPeriodError(Exception):
    code = "INVALID_PERIOD"


class VatDeclarationService:
    """Read-only aggregation feeding tờ khai 01/GTGT. R-V1..R-V5."""

    def __init__(self, *, output_source: Any, input_source: Any) -> None:
        self._output = output_source
        self._input = input_source

    def declare(self, company_id: UUID, year: int, month: int) -> dict[str, Any]:
        import calendar

        if not 1 <= month <= 12:
            raise InvalidPeriodError(f"Tháng không hợp lệ: {month}")
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])

        out_vat = Decimal(0)
        out_count = 0
        for line in self._output(company_id, start, end):
            if not str(line["account_code"]).startswith("333"):
                continue
            out_vat += Decimal(str(line["credit"])) - Decimal(str(line["debit"]))
            out_count += 1

        in_ded = Decimal(0)
        in_count = 0
        pending_excluded = 0
        for inv in self._input(company_id, start, end):
            if inv.get("status") != "POSTED":
                continue
            ded = Decimal(str(inv["vat_deductible"]))
            if inv.get("deductibility") == "DEDUCTIBLE":
                in_ded += ded
                in_count += 1
            elif inv.get("deductibility") == "PENDING_PROOF":
                pending_excluded += 1

        payable = max(Decimal(0), out_vat - in_ded)
        carry = max(Decimal(0), in_ded - out_vat)

        return {
            "period": {"year": year, "month": month},
            "output_vat": out_vat,
            "input_vat_deductible": in_ded,
            "vat_payable": payable,
            "carry_forward": carry,
            "detail": {
                "output_lines_count": out_count,
                "input_invoices_count": in_count,
                "pending_proof_excluded": pending_excluded,
            },
        }
