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
        """Build journal lines; codes maps semantic roles → account codes.

        Defaults to the TT133/SME catalog when no mapping is supplied.
        """
        from src.bricks.coa.domain import resolve_chart_role

        c = codes or {r: resolve_chart_role(r) for r in ("ar", "revenue", "vat_output")}
        revenue = sum((i.amount for i in inv.items), Decimal(0))
        vat = (revenue * inv.vat_rate).quantize(Decimal(1))
        total = revenue + vat
        lines = [
            JournalLine(account_code=c["ar"], debit=total),
            JournalLine(account_code=c["revenue"], credit=revenue),
        ]
        if vat > 0:
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
    ) -> None:
        self._fy = fy
        self._coa = coa
        self._numbering = numbering
        self._audit = audit
        self._regime_of = regime_of
        self._on_posted = on_posted
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
