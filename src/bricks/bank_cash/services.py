"""Bank & Cash services — rules per specs §5.1/§5.2 (Reconciliation later)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.bank_cash.domain import (
    CASH_CODE_RE,
    GENESIS_CHECKSUM,
    BankAccount,
    BankAccountStatus,
    CashAccount,
    CashAccountStatus,
    chain_checksum,
)


class ActorRequiredError(Exception):
    pass


class DuplicateBankAccountError(Exception):
    pass


class DuplicateCashCodeError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class NegativeBalanceError(Exception):
    pass


class SystemAccountProtectedError(Exception):
    pass


class NotFoundError(Exception):
    pass


def _require(actor: UUID | None, reason: str | None) -> tuple[UUID, str]:
    if not actor or not reason or not str(reason).strip():
        raise ActorRequiredError("actor và reason là bắt buộc")
    return actor, reason


def _stamp(
    entity: BankAccount | CashAccount,
    action: str,
    actor: UUID,
    reason: str,
) -> str:
    return chain_checksum(
        entity.checksum or GENESIS_CHECKSUM, entity.id, actor, f"{action}:{reason}"
    )


class BankAccountService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def create_bank_account(
        self,
        *,
        company_id: UUID,
        bank_name: str,
        account_number: str,
        account_holder: str,
        branch: str = "",
        is_primary: bool = False,
        actor: UUID | None,
        reason: str | None,
    ) -> BankAccount:
        actor_x, reason_x = _require(actor, reason)
        if not self._repo.validate_account_number_unique(company_id, account_number):
            raise DuplicateBankAccountError("Số TK đã tồn tại")
        acc = BankAccount(
            company_id=company_id,
            bank_name=bank_name,
            account_number=account_number,
            account_holder=account_holder,
            branch=branch,
            is_primary=is_primary,
        )
        acc.checksum = _stamp(acc, "CREATE", actor_x, reason_x)
        saved: BankAccount = self._repo.create(acc)
        if is_primary:
            prev = self._repo.find_primary(company_id)
            if prev and prev.id != acc.id:
                prev.is_primary = False
                prev.checksum = _stamp(prev, "UNSET_PRIMARY", actor_x, reason_x)
                self._repo.update(prev)
        return saved

    def get_account(self, aid: UUID) -> BankAccount | None:
        found: BankAccount | None = self._repo.get_by_id(aid)
        return found

    def list_by_company(self, cid: UUID, status: str | None = None) -> list[BankAccount]:
        out: list[BankAccount] = self._repo.get_by_company(cid)
        if status:
            out = [a for a in out if a.status.value == status]
        return out

    def set_primary(self, aid: UUID, actor: UUID, reason: str) -> BankAccount:
        actor_x, reason_x = _require(actor, reason)
        acc = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy TK ngân hàng")
        prev = self._repo.find_primary(acc.company_id)
        if prev and prev.id != acc.id:
            prev.is_primary = False
            prev.checksum = _stamp(prev, "UNSET_PRIMARY", actor_x, reason_x)
            self._repo.update(prev)
        acc.is_primary = True
        acc.checksum = _stamp(acc, "SET_PRIMARY", actor_x, reason_x)
        primed: BankAccount = self._repo.update(acc)
        return primed

    def suspend_account(self, aid: UUID, actor: UUID, reason: str) -> BankAccount:
        actor_x, reason_x = _require(actor, reason)
        acc = self._get_or_404(aid)
        acc.status = BankAccountStatus.SUSPENDED
        acc.checksum = _stamp(acc, "SUSPEND", actor_x, reason_x)
        upd: BankAccount = self._repo.update(acc)
        return upd

    def close_account(self, aid: UUID, actor: UUID, reason: str) -> BankAccount:
        """Soft-close only — 10-year retention."""
        actor_x, reason_x = _require(actor, reason)
        acc = self._get_or_404(aid)
        acc.status = BankAccountStatus.CLOSED
        acc.checksum = _stamp(acc, "CLOSE", actor_x, reason_x)
        closed_acc: BankAccount = self._repo.update(acc)
        return closed_acc

    def validate_before_entry(self, company_id: UUID, aid: UUID) -> None:
        acc = self._get_or_404(aid)
        if acc.company_id != company_id:
            raise NotFoundError("TK không thuộc công ty")
        if acc.status == BankAccountStatus.CLOSED:
            raise AccountClosedError("TK ngân hàng đã đóng")

    def _get_or_404(self, aid: UUID) -> BankAccount:
        acc: BankAccount | None = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy TK ngân hàng")
        return acc


class CashAccountService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def create_cash_account(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        opening_balance: Decimal = Decimal(0),
        actor: UUID | None = None,
        reason: str | None = None,
        is_system: bool = False,
    ) -> CashAccount:
        actor_x, reason_x = _require(actor, reason)
        if not CASH_CODE_RE.match(code or ""):
            raise ValueError(f"Mã quỹ không hợp lệ: {code}")
        if not self._repo.validate_code_unique(company_id, code):
            raise DuplicateCashCodeError("Mã quỹ đã tồn tại")
        acc = CashAccount(
            company_id=company_id,
            code=code,
            name=name.strip(),
            opening_balance=opening_balance,
            current_balance=opening_balance,
            is_system=is_system,
        )
        acc.checksum = _stamp(acc, "CREATE", actor_x, reason_x)
        created: CashAccount = self._repo.create(acc)
        return created

    def get_cash(self, aid: UUID) -> CashAccount | None:
        found: CashAccount | None = self._repo.get_by_id(aid)
        return found

    def get_by_code(self, company_id: UUID, code: str) -> CashAccount | None:
        rows: list[CashAccount] = self._repo.get_by_company(company_id)
        for acc in rows:
            if acc.code == code:
                return acc
        return None

    def apply_journal(
        self,
        company_id: UUID,
        lines: list[dict[str, str]],
        *,
        actor: UUID,
        reason: str,
        chief_approved: bool = False,
    ) -> list[CashAccount]:
        """Apply debit-credit deltas to matching cash accounts.

        All-or-nothing pre-check: any line that would overdraw without
        chief approval raises before a single balance is mutated.
        """
        targets: dict[UUID, CashAccount] = {}
        deltas: dict[UUID, Decimal] = {}
        for ln in lines:
            cash = self.get_by_code(company_id, ln["account_code"])
            if cash is None:
                continue
            delta = Decimal(str(ln["debit"])) - Decimal(str(ln["credit"]))
            if delta == 0:
                continue
            projected = cash.current_balance + delta
            if projected < 0 and not chief_approved:
                raise NegativeBalanceError(f"Quỹ {cash.code} không đủ (dự kiến {projected})")
            deltas[cash.id] = deltas.get(cash.id, Decimal(0)) + delta
            targets[cash.id] = cash
        updated: list[CashAccount] = []
        for cid_, delta in deltas.items():
            cash = targets[cid_]
            cash.apply_delta(delta)
            cash.checksum = chain_checksum(
                cash.checksum or GENESIS_CHECKSUM, cash.id, actor, reason
            )
            saved: CashAccount | None = self._repo.update(cash)
            assert saved is not None
            updated.append(saved)
        return updated

    def list_by_company(self, cid: UUID, status: str | None = None) -> list[CashAccount]:
        out: list[CashAccount] = self._repo.get_by_company(cid)
        if status:
            out = [a for a in out if a.status.value == status]
        return out

    def update_balance(
        self,
        aid: UUID,
        amount: Decimal,
        *,
        actor: UUID | None,
        reason: str | None,
        chief_approved: bool = False,
    ) -> CashAccount:
        """Delta adjust; negative result needs chief approval flag."""
        actor_x, reason_x = _require(actor, reason)
        acc = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy quỹ tiền mặt")
        projected = acc.current_balance + Decimal(str(amount))
        if projected < 0 and not chief_approved:
            raise NegativeBalanceError("Quỹ không đủ; cần Kế toán trưởng phê duyệt")
        acc.apply_delta(Decimal(str(amount)))
        acc.checksum = _stamp(acc, "BALANCE_ADJ", actor_x, reason_x)
        updated: CashAccount = self._repo.update(acc)
        return updated

    def close_cash_account(self, aid: UUID, actor: UUID, reason: str) -> CashAccount:
        actor_x, reason_x = _require(actor, reason)
        acc = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy quỹ tiền mặt")
        if acc.is_system:
            raise SystemAccountProtectedError("Tài khoản hệ thống được bảo vệ")
        acc.status = CashAccountStatus.CLOSED
        acc.checksum = _stamp(acc, "CLOSE", actor_x, reason_x)
        closed_cash: CashAccount = self._repo.update(acc)
        return closed_cash

    def validate_before_entry(self, aid: UUID) -> None:
        acc = self._repo.get_by_id(aid)
        if acc is None:
            raise NotFoundError("Không tìm thấy quỹ tiền mặt")
        if acc.status == CashAccountStatus.CLOSED:
            raise AccountClosedError("Quỹ đã đóng")
