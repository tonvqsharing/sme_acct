"""SystemSettings service — VAT rate validation + e-invoice series SOD."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.system_settings.domain import (
    CompanyConfig,
    EInvoiceSeries,
    InvalidRegimeError,
)
from src.bricks.system_settings.domain import (
    FlagLockedError as DomainFlagLockedError,
)


class MaxSeriesExceededError(Exception):
    code = "MAX_SERIES_EXCEEDED"


class DuplicateSeriesPrefixError(Exception):
    code = "DUPLICATE_SERIES_PREFIX"


class SodViolationError(Exception):
    code = "SOD_VIOLATION"


class ConfigVersionConflictError(Exception):
    code = "CONFIG_VERSION_CONFLICT"


class WindowNotFoundError(Exception):
    code = "WINDOW_NOT_FOUND"


# Re-export domain exception for backward compatibility
FlagLockedError = DomainFlagLockedError


# Base rates per Luật GTGT 2024 + reduced 8% per NQ 204/2025/QH15 /
# NĐ 174/2025/NĐ-CP (eff → 31/12/2026). NOT_TAXED(-1) remains an
# item-level exemption flag, not a configurable deductible rate.
LAWFUL_RATES = frozenset({0, 5, 8, 10})
MAX_SERIES = 15


class SystemSettingsService:
    def __init__(self, repo: Any, period_lock_repo: Any = None) -> None:
        self._repo = repo
        self._period_lock_repo = period_lock_repo

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
        raise DomainFlagLockedError(
            "vat_rates là LAW-type; thay đổi chỉ qua migration có phê duyệt"
        )

    # ── Period lock (P0-02) ─────────────────────────────────────────────
    def is_period_locked(self, company_id: UUID, fiscal_year: int, period: int) -> bool:
        """Check if a period is locked for posting."""
        if self._period_lock_repo is None:
            return False
        result: bool = self._period_lock_repo.is_locked(company_id, fiscal_year, period)
        return result

    def lock_period(
        self,
        company_id: UUID,
        fiscal_year: int,
        period: int,
        actor: UUID,
        notes: str | None = None,
    ) -> None:
        """Lock a period. Requires ACCOUNTANT+ role (checked at API layer)."""
        if not 1 <= period <= 12:
            raise InvalidPeriodError(f"Period must be 1-12, got {period}")
        if self._period_lock_repo is None:
            raise RuntimeError("PeriodLockRepository not initialized")
        self._period_lock_repo.lock(company_id, fiscal_year, period, actor, notes=notes)

    def unlock_period(
        self,
        company_id: UUID,
        fiscal_year: int,
        period: int,
    ) -> bool:
        """Unlock a period. Returns True if was locked."""
        if self._period_lock_repo is None:
            return False
        result2: bool = self._period_lock_repo.unlock(company_id, fiscal_year, period)
        return result2

    def list_locked_periods(
        self,
        company_id: UUID,
        fiscal_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """List all locked periods for a company."""
        if self._period_lock_repo is None:
            return []
        result3: list[dict[str, Any]] = self._period_lock_repo.list_locked(company_id, fiscal_year)
        return result3

    # ── Config flags (CONFIG-type) ──────────────────────────────────────
    def update_config_flag(
        self,
        company_id: UUID,
        flag_name: str,
        value: Any,
        actor: UUID,
        config_version: int,
    ) -> CompanyConfig:
        """Update a CONFIG-type flag with optimistic locking."""
        cfg = self.get_config(company_id)
        if cfg.config_version != config_version:
            raise ConfigVersionConflictError(
                f"Config version mismatch: expected {config_version}, got {cfg.config_version}"
            )
        # Update the config with the new flag value
        updated = cfg.with_flag_update(flag_name, value, actor)
        saved: CompanyConfig = self._repo.update_config(updated)
        return saved

    # ── Legal review stamp ──────────────────────────────────────────────
    def legal_review(
        self,
        company_id: UUID,
        actor: UUID,
    ) -> CompanyConfig:
        """Mark config as legally reviewed by Chief Accountant."""
        from datetime import UTC, datetime

        cfg = self.get_config(company_id)
        updated = cfg.with_legal_review(actor, datetime.now(UTC))
        saved2: CompanyConfig = self._repo.update_config(updated)
        return saved2

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
    """Aggregation feeding tờ khai 01/GTGT. R-V1..R-V5. Persists carry-forward."""

    def __init__(
        self,
        *,
        output_source: Any,
        input_source: Any,
        carry_repo: Any | None = None,
        config_repo: Any | None = None,
    ) -> None:
        self._output = output_source
        self._input = input_source
        self._carry_repo = carry_repo
        self._config_repo = config_repo

    def _compute(
        self,
        company_id: UUID,
        year: int,
        month: int | None = None,
        quarter: int | None = None,
    ) -> dict[str, Any]:
        """Pure calc without side-effects (for export)."""
        import calendar

        if month is not None and quarter is not None:
            raise InvalidPeriodError("Chỉ chọn tháng HOẶC quý")
        if month is None and quarter is None:
            raise InvalidPeriodError("Cần chỉ định tháng hoặc quý")

        months: list[int]
        if quarter is not None:
            if not 1 <= quarter <= 4:
                raise InvalidPeriodError(f"Quý không hợp lệ: {quarter}")
            months = list(range(int(quarter) * 3 - 2, int(quarter) * 3 + 1))
        else:
            assert month is not None  # narrowed: one of month/quarter must be set
            if not 1 <= month <= 12:
                raise InvalidPeriodError(f"Tháng không hợp lệ: {month}")
            months = [month]

        # Enforce vat_settlement_cycle if config available
        if self._config_repo is not None:
            try:
                cfg = self._config_repo.get_config(company_id)
                cycle = getattr(cfg, "vat_settlement_cycle", None)
                if cycle == "monthly" and quarter is not None:
                    raise InvalidPeriodError("Công ty kê khai theo tháng, không được kê theo quý")
                if cycle == "quarterly" and month is not None:
                    raise InvalidPeriodError("Công ty kê khai theo quý, không được kê theo tháng")
            except InvalidPeriodError:
                raise
            except Exception:  # noqa: BLE001 — config unavailable is non-fatal
                import logging

                logging.getLogger(__name__).warning(
                    "vat_settlement_cycle check skipped: config unavailable",
                    extra={"company_id": str(company_id)},
                )

        # Previous carry (if persisted)
        prev_carry = Decimal(0)
        if self._carry_repo is not None:
            prev_carry = self._carry_repo.get_previous_carry(
                company_id, year, month if quarter is None else None, quarter
            )

        out_vat = Decimal(0)
        in_ded = prev_carry  # carry from previous period is deductible this period
        out_count = 0
        in_count = 0
        pending_excluded = 0
        for m in months:
            m_start = date(year, m, 1)
            m_end = date(year, m, calendar.monthrange(year, m)[1])
            for line in self._output(company_id, m_start, m_end):
                if not str(line["account_code"]).startswith("333"):
                    continue
                out_vat += Decimal(str(line["credit"])) - Decimal(str(line["debit"]))
                out_count += 1
            for inv in self._input(company_id, m_start, m_end):
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

        period_info: dict[str, Any] = {"year": year}
        if quarter is not None:
            period_info["quarter"] = quarter
        else:
            period_info["month"] = month

        return {
            "period": period_info,
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

    def declare(
        self,
        company_id: UUID,
        year: int,
        month: int | None = None,
        quarter: int | None = None,
    ) -> dict[str, Any]:
        """Monthly or quarterly VAT declaration (§Addendum — quarterly). Persists carry."""
        d = self._compute(company_id, year, month=month, quarter=quarter)
        # Persist carry for next period
        if self._carry_repo is not None:
            self._carry_repo.save_carry(
                company_id,
                year,
                d["period"].get("month"),
                d["period"].get("quarter"),
                d["carry_forward"],
            )
        return d

    def export_gdt_xml(
        self, company_id: UUID, year: int, month: int | None = None, quarter: int | None = None
    ) -> str:
        """Export 01/GTGT as GDT-compatible XML for thuedientu.gdt.gov.vn."""
        import xml.sax.saxutils as _esc

        d = self._compute(company_id, year, month=month, quarter=quarter)
        period = d["period"]
        tag = f"Q{period['quarter']}" if "quarter" in period else f"M{period['month']}"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<ToKhai01GTGT nam="{_esc.escape(str(period["year"]))}" ky="{_esc.escape(tag)}">'
            f"<ThueDauRa>{_esc.escape(str(d['output_vat']))}</ThueDauRa>"
            f"<ThueDauVaoKhauTru>{_esc.escape(str(d['input_vat_deductible']))}</ThueDauVaoKhauTru>"
            f"<ThuePhaiNop>{_esc.escape(str(d['vat_payable']))}</ThuePhaiNop>"
            f"<ThueKhauTruKySau>{_esc.escape(str(d['carry_forward']))}</ThueKhauTruKySau>"
            "</ToKhai01GTGT>"
        )


# ═══ Tax-rate catalog — effective-dated master data ═══════════════════════


class DuplicateWindowError(Exception):
    code = "DUPLICATE_WINDOW"


class TaxRateCatalogService:
    """Governance for date-effective rate windows.

    Vietnamese-standard pattern (cf. danh mục thuế suất in MISA/Fast):
    catalog seeded from statute, extended/closed by governed events with
    SOD approval; never deleted — expired rows remain as history of what
    applied when.
    """

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def ensure_seeded(self) -> None:
        """Idempotent: insert statute windows only when table is empty."""
        if self._repo.count() > 0:
            return
        for w in __import__(
            "src.bricks.system_settings.rate_windows",
            fromlist=["SEED_TAX_RATE_WINDOWS"],
        ).SEED_TAX_RATE_WINDOWS:
            self._repo.add(w)

    def all_windows(self) -> list[Any]:
        rows: list[Any] = self._repo.all()
        return rows

    def applicable_fractions(self, on_date: date) -> frozenset[str]:
        self.ensure_seeded()
        return frozenset(w.fraction for w in self.all_windows() if w.covers(on_date))

    def add_window(
        self,
        window: Any,
        *,
        actor: UUID,
        approver: UUID,
    ) -> Any:
        """New law event → new window row. SOD + overlap guard."""
        if approver == actor:
            raise SodViolationError("Cần người phê duyệt khác người thực hiện")
        self.ensure_seeded()
        for existing in self._repo.all():
            if existing.fraction != window.fraction:
                continue
            a_from = window.valid_from or date.min
            a_to = window.valid_to or date.max
            e_from = existing.valid_from or date.min
            e_to = existing.valid_to or date.max
            if a_from <= e_to and e_from <= a_to:
                raise ValueError(
                    f"Window cho {window.fraction} chồng lấn "
                    f"{e_from}..{e_to} ({existing.decree_ref})"
                )
        return self._repo.add(window)

    def close_window(self, fraction: str, *, end_on: date, actor: UUID, approver: UUID) -> Any:
        """Shorten valid_to (early repeal). SOD; keeps history."""
        if approver == actor:
            raise SodViolationError("Cần người phê duyệt khác người thực hiện")
        for w in self.all_windows():
            if w.fraction == fraction and (w.valid_to is None or w.valid_to > end_on):
                closed = replace(w, valid_to=end_on)
                self._repo.remove(w)
                return self._repo.add(closed)
        raise WindowNotFoundError(f"Không tìm thấy cửa sổ thuế suất {fraction}")
