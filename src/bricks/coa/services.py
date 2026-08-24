"""COA services — CRUD + hierarchy rules."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.bricks.coa.domain import (
    CODE_RE,
    Account,
    AccountStatus,
    NormalBalance,
)


class DuplicateAccountError(Exception):
    pass


class ParentNotFoundError(Exception):
    pass


class ParentNotAggregateError(Exception):
    """Detail (4-digit) accounts may only nest under 3-digit parents."""


class CircularParentError(Exception):
    pass


def _require(actor: object, reason: object) -> tuple[object, object]:
    if not actor or not reason or not reason.strip():
        raise ValueError("actor and reason are required")
    return actor, reason


class AccountService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def create_account(
        self,
        company_id: UUID,
        code: str,
        name: str,
        normal_balance: str = "debit",
        parent_code: str | None = None,
        actor: object = None,
        reason: object = None,
    ) -> Account:
        _require(actor, reason)
        if not CODE_RE.match(code):
            raise ValueError(f"Invalid account code: {code}")
        if not self._repo.validate_code_unique(company_id, code):
            raise DuplicateAccountError(f"Code {code} already exists")
        nb = NormalBalance(normal_balance)
        if parent_code:
            parent = self._repo.get_by_code(company_id, parent_code)
            if parent is None:
                raise ParentNotFoundError(parent_code)
            if len(code) == 4 and len(parent_code) != 3:
                raise ParentNotAggregateError(parent_code)
        account = Account(
            company_id=company_id,
            code=code,
            name=name.strip(),
            normal_balance=nb,
            parent_code=parent_code,
        )
        created: Account = self._repo.create(account)
        return created

    def get_account(self, company_id: UUID, code: str) -> Account | None:
        found: Account | None = self._repo.get_by_code(company_id, code)
        return found

    def list_accounts(self, company_id: UUID) -> list[Account]:
        out: list[Account] = self._repo.get_by_company(company_id)
        return out

    def deactivate_account(
        self,
        company_id: UUID,
        code: str,
        *,
        actor: object = None,
        reason: object = None,
    ) -> Account:
        _require(actor, reason)
        # Aggregate accounts with active children cannot be deactivated.
        children = [
            a
            for a in self._repo.get_by_company(company_id)
            if a.parent_code == code and a.status == AccountStatus.ACTIVE
        ]
        if children:
            from src.bricks.coa.services import HasActiveChildrenError

            raise HasActiveChildrenError(code)
        account = self._repo.get_by_code(company_id, code)
        if account is None:
            from src.bricks.coa.services import AccountNotFoundError

            raise AccountNotFoundError(code)
        account.status = AccountStatus.INACTIVE
        updated: Account = self._repo.update(account)
        return updated

    def validate_posting_account(self, company_id: UUID, code: str) -> None:
        """Only ACTIVE detail (4-digit) accounts accept journal lines."""
        account = self._repo.get_by_code(company_id, code)
        if account is None:
            from src.bricks.coa.services import AccountNotFoundError

            raise AccountNotFoundError(code)
        if account.status != AccountStatus.ACTIVE:
            from src.bricks.coa.services import InactiveAccountError

            raise InactiveAccountError(code)
        if not account.is_detail:
            from src.bricks.coa.services import AggregateAccountError

            raise AggregateAccountError(code)


class AccountNotFoundError(Exception):
    pass


class HasActiveChildrenError(Exception):
    pass


class InactiveAccountError(Exception):
    pass


class AggregateAccountError(Exception):
    pass
