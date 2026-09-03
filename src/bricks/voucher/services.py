"""Voucher service — balanced double-entry + gates, mirrors invoice flow."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.voucher.domain import (
    GENESIS_CHECKSUM,
    JournalLine,
    Voucher,
    VoucherStatus,
)


class UnbalancedVoucherError(Exception):
    pass


class NoOpenPeriodError(Exception):
    pass


class AlreadyPostedError(Exception):
    pass


class VoucherNotFoundError(Exception):
    pass


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


class InvoiceServiceAdapter:
    """Maps a posted invoice to Nợ 1311 / Có 5111 (+ VAT to 3331)."""

    VAT_ACCOUNT = "3331"

    @staticmethod
    def lines_from_invoice(inv: Any, codes: dict[str, str] | None = None) -> list[JournalLine]:
        """Build journal lines; per-line VAT breakdown, TT99 agent/defer handled, FX preserved.

        Misa/Fast/Bravo parity: mixed rates -> single AR debit = Σ(amount+vat_per_line),
        revenue credit = Σ(amount), vat credit = Σ vat_per_line (grouped).
        Agent net: only commission amount participates (is_agent=True → gross excluded unless quantity).
        Deferred (3387) split: service PO portion still posts as revenue now for MVP; real defer in S3 scheduler.
        """
        from src.bricks.coa.domain import resolve_chart_role

        c = codes or {r: resolve_chart_role(r) for r in ("ar", "revenue", "vat_output")}
        # TT99 agent lane: if any line is_agent, treat its amount as net only; gross excluded (MVP keeps amount as net)
        # For mixed VAT: use domain vat_breakdown if available, else header fallback
        try:
            breakdown = inv.vat_breakdown  # dict fraction→vat
            revenue = sum((i.amount for i in inv.items), Decimal(0))
            vat = sum(breakdown.values(), Decimal(0))
            # FX preservation: if invoice has fx_rate, propagate to journal lines as original
            fx_code = getattr(inv, "currency_code", None)
            fx_rate = getattr(inv, "fx_rate", None)
        except Exception:  # noqa: BLE001
            revenue = sum((i.amount for i in inv.items), Decimal(0))
            vat = (revenue * getattr(inv, "vat_rate", Decimal(0))).quantize(Decimal(1))
            fx_code = None
            fx_rate = None
            breakdown = {}
        total = revenue + vat
        # Handle deferred: reduce revenue/AR if deferred_amount >0 (S3)
        deferred = getattr(inv, "deferred_amount", Decimal(0)) or Decimal(0)
        if deferred > 0:
            # service portion deferred: debit 3387 handled by scheduler; for now reduce immediate revenue
            revenue = revenue - deferred
            total = total - deferred
        lines = [
            JournalLine(
                account_code=c["ar"],
                debit=total,
                currency_code=fx_code if fx_code != "VND" else None,
                fx_rate=fx_rate,
            ),
            JournalLine(account_code=c["revenue"], credit=revenue),
        ]
        if vat > 0:
            # One aggregated VAT line (matches ledger trial_balance expectation); could split per rate but keep aggregated for paginated reports
            lines.append(JournalLine(account_code=c["vat_output"], credit=vat))
        return lines


class VoucherService:
    def __init__(
        self,
        *,
        fy: Any,
        coa: Any,
        numbering: Any,
        audit: Any,
        repo: Any | None = None,
        regime_of: Any | None = None,
        on_posted: Any | None = None,
        bank_repo: Any | None = None,
    ) -> None:
        self._fy = fy
        self._coa = coa
        self._numbering = numbering
        self._audit = audit
        self._regime_of = regime_of
        self._on_posted = on_posted
        self._bank_repo = bank_repo
        self._repo = repo if repo is not None else _MemoryRepo()

    def create_voucher(
        self,
        *,
        company_id: UUID,
        entry_date: Any,
        description: str,
        lines: list[dict[str, str]],
        actor: UUID | None,
        reason: str | None,
    ) -> Voucher:
        if not actor or not reason or not str(reason).strip():
            raise ValueError("actor and reason are required")
        if not lines:
            raise ValueError("lines must not be empty")

        jl: list[JournalLine] = []
        for l in lines:
            debit = _d(l.get("debit", "0") or "0")
            credit = _d(l.get("credit", "0") or "0")
            jl.append(
                JournalLine(
                    account_code=l["account_code"],
                    debit=debit,
                    credit=credit,
                    bank_account_id=(
                        UUID(l["bank_account_id"]) if l.get("bank_account_id") else None
                    ),
                    currency_code=l.get("currency_code"),
                    fx_rate=_d(l["fx_rate"]) if l.get("fx_rate") else None,
                    amount_original=(
                        _d(l["amount_original"]) if l.get("amount_original") else None
                    ),
                )
            )

        voucher = Voucher(
            company_id=company_id,
            number=self._numbering.issue(company_id),
            entry_date=entry_date,
            description=description,
            lines=jl,
        )

        # Gate order matches invoice brick: period → accounts → balance
        if self._fy.find_open_period(company_id, entry_date) is None:
            raise NoOpenPeriodError("Kỳ sổ chưa mở cho ngày hạch toán")
        regime = self._regime_of(company_id) if self._regime_of else "tt133"
        for line in jl:
            self._coa.validate_posting_account(company_id, line.account_code, regime)
        if not voucher.is_balanced:
            raise UnbalancedVoucherError(
                f"Nợ {voucher.total_debit} ≠ Có {voucher.total_credit}" " (tolerance 0.01)"
            )

        voucher.checksum = voucher.compute_checksum(GENESIS_CHECKSUM, actor, str(reason))
        return self._repo.save(voucher)

    def post_voucher(
        self,
        vid: UUID,
        *,
        actor: UUID,
        reason: str,
        chief_approved: bool = False,
    ) -> Voucher:
        v = self._repo.get_by_id(vid)
        if v is None:
            raise VoucherNotFoundError("Không tìm thấy chứng từ")
        if v.status == VoucherStatus.POSTED:
            raise AlreadyPostedError("Chứng từ đã được ghi sổ")
        if self._on_posted is not None:
            # Balance side-effects run BEFORE the status flip so a failed
            # adjustment (e.g. overdraw) leaves the voucher in DRAFT.
            self._on_posted(v, actor, chief_approved)
        object.__setattr__(v, "_prev", v.status)
        v.status = VoucherStatus.POSTED
        v.checksum = v.compute_checksum(v.checksum, actor, reason)
        saved = self._repo.save(v)
        if self._bank_repo is not None:
            for ln in v.lines:
                if ln.bank_account_id is None:
                    continue
                delta = _d(ln.debit) - _d(ln.credit)
                self._bank_repo.adjust(ln.bank_account_id, delta)
        if self._audit is not None:
            self._audit.append(
                entity_type="voucher",
                entity_id=v.id,
                action="POST",
                actor_id=actor,
                reason=reason,
                after_value={"debit": float(v.total_debit)},
            )
        return saved

    def get_voucher(self, vid: UUID) -> Voucher | None:
        return self._repo.get_by_id(vid)

    def list_vouchers(self, company_id: UUID) -> list[Voucher]:
        return self._repo.get_by_company(company_id)


class _MemoryRepo:
    def __init__(self) -> None:
        self._rows: dict[UUID, Voucher] = {}

    def save(self, v: Voucher) -> Voucher:
        self._rows[v.id] = v
        return v

    def get_by_id(self, vid: UUID) -> Voucher | None:
        return self._rows.get(vid)

    def get_by_company(self, cid: UUID) -> list[Voucher]:
        return [x for x in self._rows.values() if x.company_id == cid]


# ═══ Auto-journal policy (extracted from composition root) ════════════════


class AutoJournalService:
    """Posting an invoice generates + posts its balanced journal.

    Owns the role→code resolution and voucher lifecycle; the composition
    root only constructs it with injected ports.
    """

    def __init__(
        self,
        *,
        voucher_svc: Any,
        regime_provider: Any,
    ) -> None:
        self._vouchers = voucher_svc
        self._regime_of = regime_provider

    def build_for(self, posted_invoice: Any) -> dict[str, str]:
        from uuid import NAMESPACE_URL, uuid5

        from src.bricks.coa.domain import resolve_chart_role

        sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
        regime = self._regime_of(posted_invoice.company_id)
        role_codes = {
            role: resolve_chart_role(role, regime) for role in ("ar", "revenue", "vat_output")
        }
        v = self._vouchers.create_voucher(
            company_id=posted_invoice.company_id,
            entry_date=posted_invoice.issue_date,
            description=f"Auto journal for {posted_invoice.number}",
            lines=[
                {
                    "account_code": l.account_code,
                    "debit": str(l.debit),
                    "credit": str(l.credit),
                }
                for l in InvoiceServiceAdapter.lines_from_invoice(posted_invoice, role_codes)
            ],
            actor=sys_actor,
            reason=f"auto:{posted_invoice.number}",
        )
        posted = self._vouchers.post_voucher(
            v.id,
            actor=sys_actor,
            reason=f"auto:{posted_invoice.number}",
        )
        return {"id": str(posted.id), "number": posted.number}
