"""Purchase service — gates + lifecycle per docs/purchases/specs §5."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.purchases.domain import (
    GENESIS_CHECKSUM,
    PaymentMethod,
    PurchaseStatus,
    SupplierInvoice,
    SupplierLine,
)

# ── Exceptions → API codes (EX-P01..P07) ──────────────────────────────────


class MissingActorError(Exception):
    code = "MISSING_ACTOR"


class DuplicateInvoiceError(Exception):
    code = "DUPLICATE_INVOICE"


class PeriodClosedError(Exception):
    code = "PERIOD_CLOSED"


class InvalidAccountError(Exception):
    code = "INVALID_ACCOUNT"


class TotalMismatchError(Exception):
    code = "TOTAL_MISMATCH"


class AlreadyPostedError(Exception):
    code = "ALREADY_POSTED"


class NotPostedError(Exception):
    code = "NOT_POSTED_ON_CANCEL"


class NotFoundError(Exception):
    code = "NOT_FOUND"


def _require(actor: UUID | None, reason: str | None) -> tuple[UUID, str]:
    if actor is None or not reason or not reason.strip():
        raise MissingActorError("actor là bắt buộc")
    return actor, reason


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


class PurchaseService:
    """Gate order per spec §5: FY period → COA accounts → duplicate → totals."""

    def __init__(
        self,
        *,
        repo: Any,
        fy: Any,
        coa: Any,
        regime_of: Any | None = None,
        audit: Any | None = None,
        allowed_vat_rates: frozenset[str] | None = None,
        rate_gate: Any | None = None,
    ) -> None:
        raw = allowed_vat_rates or DEFAULT_ALLOWED_VAT_RATES
        self._allowed_vat_rates = frozenset(str(_d(r)) for r in raw)
        self._rate_gate = rate_gate
        self._repo = repo
        self._fy = fy
        self._coa = coa
        self._regime_of = regime_of
        self._audit = audit

    # ── helpers ────────────────────────────────────────────────────────
    def _regime(self, company_id: UUID) -> str:
        return self._regime_of(company_id) if self._regime_of else "tt133"

    def _stamp(self, inv: SupplierInvoice, action: str, actor: UUID, reason: str) -> str:
        return inv.compute_checksum(inv.checksum or GENESIS_CHECKSUM, actor, action, reason)

    def _log(self, action: str, entity_id: UUID, actor: UUID, reason: str) -> None:
        if self._audit is not None:
            self._audit.append(
                entity_type="purchase_invoice",
                entity_id=entity_id,
                action=action,
                actor_id=actor,
                reason=reason,
                after_value=None,
            )

    # ── create ─────────────────────────────────────────────────────────
    def create_invoice(
        self,
        *,
        company_id: UUID,
        supplier_name: str,
        supplier_mst: str,
        invoice_number: str,
        invoice_symbol: str,
        invoice_date: date,
        entry_date: date,
        payment_method: str = "none",
        payment_proof: bool = False,
        lines: list[dict[str, str]],
        expected_total_payment: str | None = None,
        actor: UUID | None = None,
        reason: str | None = None,
    ) -> SupplierInvoice:
        actor_x, reason_x = _require(actor, reason)

        # Gate 1 — fiscal period open
        if self._fy.find_open_period(company_id, entry_date) is None:
            raise PeriodClosedError("Kỳ sổ chưa mở")

        # Gate 2 — COA posting accounts under the company's regime
        regime = self._regime(company_id)
        for l in lines:
            from src.bricks.coa.services import (
                AccountNotFoundError,
                AggregateAccountError,
                InactiveAccountError,
            )

            try:
                self._coa.validate_posting_account(company_id, l["expense_account"], regime)
            except ValueError as exc:
                raise InvalidAccountError(str(exc)) from exc
            except (
                AccountNotFoundError,
                AggregateAccountError,
                InactiveAccountError,
            ) as exc:
                raise InvalidAccountError(str(exc)) from exc

        # Gate 3 — duplicate key (R-P1)
        if self._repo.exists_duplicate(company_id, supplier_mst, invoice_number, invoice_symbol):
            raise DuplicateInvoiceError("Trùng số/ký hiệu hóa đơn đã nhập")

        jl: list[SupplierLine] = []
        for l in lines:
            rate_str = str(_d(l.get("vat_rate", "0")))
            if rate_str not in self._allowed_vat_rates:
                raise ValueError(
                    f"vat_rate {rate_str} không thuộc catalog thuế suất "
                    f"({sorted(self._allowed_vat_rates)})"
                )
            if self._rate_gate is not None:
                self._rate_gate(rate_str, entry_date)
            jl.append(
                SupplierLine(
                    expense_account=l["expense_account"],
                    description=l.get("description", ""),
                    amount_pre_vat=_d(l["amount_pre_vat"]),
                    vat_rate=_d(rate_str),
                    deductible=bool(l.get("deductible", True)),
                )
            )
        inv = SupplierInvoice(
            company_id=company_id,
            supplier_name=supplier_name.strip(),
            supplier_mst=supplier_mst.strip(),
            invoice_number=invoice_number.strip(),
            invoice_symbol=invoice_symbol.strip(),
            invoice_date=invoice_date,
            entry_date=entry_date,
            lines=jl,
            payment_method=PaymentMethod(payment_method or "none"),
            payment_proof=bool(payment_proof),
        )

        # Gate 4 — totals recompute vs optional client declaration
        if expected_total_payment is not None and _d(expected_total_payment) != inv.total_payment:
            raise TotalMismatchError("Tổng thanh toán không khớp dòng chi tiết")

        inv.checksum = self._stamp(inv, "CREATE", actor_x, reason_x)
        saved: SupplierInvoice = self._repo.create(inv)
        self._log("CREATE", saved.id, actor_x, reason_x)
        return saved

    # ── queries ────────────────────────────────────────────────────────
    def get(self, iid: UUID) -> SupplierInvoice | None:
        found: SupplierInvoice | None = self._repo.get_by_id(iid)
        return found

    def list_by_company(
        self,
        cid: UUID,
        status: str | None = None,
        deductibility: str | None = None,
    ) -> list[SupplierInvoice]:
        out: list[SupplierInvoice] = self._repo.get_by_company(cid)
        if status:
            out = [x for x in out if x.status.value == status]
        if deductibility:
            out = [x for x in out if x.deductibility.value == deductibility]
        return out

    # ── lifecycle ──────────────────────────────────────────────────────
    def post(self, iid: UUID, actor: UUID, reason: str) -> SupplierInvoice:
        actor_x, reason_x = _require(actor, reason)
        inv = self._get_or_404(iid)
        if inv.status == PurchaseStatus.POSTED:
            raise AlreadyPostedError("Hóa đơn đã ghi sổ")
        if inv.status == PurchaseStatus.CANCELLED:
            raise AlreadyPostedError("Hóa đơn đã hủy")
        inv.status = PurchaseStatus.POSTED
        inv.checksum = self._stamp(inv, "POST", actor_x, reason_x)
        saved: SupplierInvoice = self._repo.update(inv)
        self._log("POST", saved.id, actor_x, reason_x)
        return saved

    def cancel(self, iid: UUID, actor: UUID, reason: str) -> SupplierInvoice:
        actor_x, reason_x = _require(actor, reason)
        inv = self._get_or_404(iid)
        if inv.status != PurchaseStatus.POSTED:
            raise NotPostedError("Chỉ hủy hóa đơn đã ghi sổ")
        inv.status = PurchaseStatus.CANCELLED
        inv.checksum = self._stamp(inv, "CANCEL", actor_x, reason_x)
        saved: SupplierInvoice = self._repo.update(inv)
        self._log("CANCEL", saved.id, actor_x, reason_x)
        return saved

    def validate_before_entry(self, company_id: UUID, iid: UUID) -> None:
        inv = self._get_or_404(iid)
        if inv.company_id != company_id:
            raise NotFoundError("Không thuộc công ty")
        if inv.status != PurchaseStatus.POSTED:
            raise NotPostedError("Chưa ghi sổ")

    def _get_or_404(self, iid: UUID) -> SupplierInvoice:
        inv: SupplierInvoice | None = self._repo.get_by_id(iid)
        if inv is None:
            raise NotFoundError("Không tìm thấy hóa đơn mua vào")
        return inv


from src.bricks.system_settings.contract import (
    ALLOWED_VAT_FRACTIONS as DEFAULT_ALLOWED_VAT_RATES,
)
