"""Opening balance service — batch lifecycle + trial gate + voucher guard."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.opening_balance.domain import (
    GENESIS_CHECKSUM,
    TOLERANCE,
    BankOpening,
    BatchSource,
    BatchState,
    GLBalance,
    OpeningBatch,
)


class BatchLockedError(Exception):
    pass


class UnbalancedOpeningError(Exception):
    pass


class NotFoundError(Exception):
    pass


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


class OpeningService:
    def __init__(
        self,
        *,
        repo: Any,
        fy_years: Any,
        coa: Any,
        regime_of: Any | None = None,
        audit: Any | None = None,
    ) -> None:
        self._repo = repo
        self._fy_years = fy_years
        self._coa = coa
        self._regime_of = regime_of
        self._audit = audit

    # ── helpers ───────────────────────────────────────────────────────
    def _regime(self, company_id: UUID) -> str:
        return self._regime_of(company_id) if self._regime_of else "tt133"

    def _log(self, action: str, entity_id: UUID, actor: UUID, reason: str) -> None:
        if self._audit is not None:
            self._audit.append(
                entity_type="opening_batch",
                entity_id=entity_id,
                action=action,
                actor_id=actor,
                reason=reason,
                after_value=None,
            )

    def _get_draft(self, batch_id: UUID) -> OpeningBatch:
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        assert isinstance(b, OpeningBatch)
        if b.state != BatchState.DRAFT:
            raise BatchLockedError("Batch is LOCKED")
        return b

    # ── batch ─────────────────────────────────────────────────────────
    def create_batch(
        self,
        *,
        company_id: UUID,
        fiscal_year_id: UUID,
        source: str = "MANUAL",
        actor: UUID,
        reason: str,
    ) -> OpeningBatch:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        fy = self._fy_years.get_by_id(fiscal_year_id)
        if fy is None or fy.company_id != company_id:
            raise NotFoundError("fiscal year not found in company")
        try:
            src = BatchSource(source)
        except ValueError:
            raise ValueError(f"source {source} invalid (MANUAL/EXCEL/YEAR_ROLL)")
        b = OpeningBatch(company_id=company_id, fiscal_year_id=fiscal_year_id, source=src)
        b.checksum = b.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        self._repo.create_batch(b)
        self._log("CREATE", b.id, actor, reason)
        return b

    # ── rows ──────────────────────────────────────────────────────────
    def post_gl(
        self, batch_id: UUID, *, lines: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        b = self._get_draft(batch_id)
        regime = self._regime(b.company_id)
        for ln in lines:
            self._coa.validate_posting_account(b.company_id, ln["account_code"], regime)
            row = GLBalance(
                batch_id=b.id,
                account_code=ln["account_code"],
                debit=_d(ln.get("debit", "0") or "0"),
                credit=_d(ln.get("credit", "0") or "0"),
                currency_code=ln.get("currency_code", "VND"),
            )
            self._repo.add_gl(row)
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_GL", b.id, actor, reason)

    def post_bank(
        self, batch_id: UUID, *, rows: list[dict[str, Any]], actor: UUID, reason: str
    ) -> None:
        b = self._get_draft(batch_id)
        for r in rows:
            row = BankOpening(
                batch_id=b.id,
                bank_account_id=UUID(str(r["bank_account_id"])),
                amount=_d(r["amount"]),
            )
            self._repo.add_bank(row)
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("POST_BANK", b.id, actor, reason)

    # ── reconcile + lock ──────────────────────────────────────────────
    def reconcile(self, batch_id: UUID) -> dict[str, Any]:
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        gl = self._repo.list_gl(batch_id)
        debit = sum((r.debit for r in gl), Decimal(0))
        credit = sum((r.credit for r in gl), Decimal(0))
        bank = self._repo.list_bank(batch_id)
        bank_total = sum((r.amount for r in bank), Decimal(0))
        balanced = abs(debit - credit) <= TOLERANCE
        return {
            "balanced": balanced,
            "debit_total": debit,
            "credit_total": credit,
            "checks": {"bank_total": bank_total, "gl_lines": len(gl)},
        }

    def lock(self, batch_id: UUID, *, actor: UUID, reason: str) -> OpeningBatch:
        b = self._get_draft(batch_id)
        rep = self.reconcile(batch_id)
        if not rep["balanced"]:
            raise UnbalancedOpeningError(f"Nợ {rep['debit_total']} ≠ Có {rep['credit_total']}")
        b.state = BatchState.LOCKED
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("LOCK", b.id, actor, reason)
        return b

    def reopen(
        self, batch_id: UUID, *, actor: UUID, reason: str, is_chief: bool = False
    ) -> OpeningBatch:
        if not is_chief:
            raise PermissionError("Only CHIEF_ACCOUNTANT can reopen")
        b = self._repo.get_batch(batch_id)
        if b is None:
            raise NotFoundError("Không tìm thấy batch số dư đầu kỳ")
        assert isinstance(b, OpeningBatch)
        b.state = BatchState.DRAFT
        b.checksum = b.compute_checksum(b.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_batch(b)
        self._log("REOPEN", b.id, actor, reason)
        return b

    def is_locked(self, company_id: UUID) -> bool | None:
        """Voucher gate: None = no batches (skip), False/True otherwise."""
        batches = self._repo.list_batches(company_id)
        if not batches:
            return None
        return any(b.state == BatchState.LOCKED for b in batches)
