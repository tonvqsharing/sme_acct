"""Party service — MST validate, duplicate 409, company isolation."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from src.bricks.party.domain import GENESIS_CHECKSUM, Department, Party


def _valid_mst(mst: str) -> bool:
    s = mst.replace("-", "").replace(" ", "")
    if re.match(r"^[1-9]\d{2}(-\d{3})?$", mst):
        return True
    if s.isdigit() and len(s) in (10, 13, 14):
        if s == "0" * len(s):
            return False
        return not s.startswith("000")
    return False


class DuplicateCodeError(Exception):
    pass


class DuplicateMstError(Exception):
    pass


class NotFoundError(Exception):
    pass


class PartyService:
    def __init__(self, *, repo: Any, audit: Any | None = None) -> None:
        self._repo = repo
        self._audit = audit

    def create_party(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        mst: str | None = None,
        address: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_customer: bool = False,
        is_supplier: bool = False,
        is_employee: bool = False,
        actor: UUID,
        reason: str,
    ) -> Party:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        if self._repo.get_by_code(company_id, code) is not None:
            raise DuplicateCodeError(f"Party code {code} đã tồn tại")
        if mst and not _valid_mst(mst):
            raise ValueError(f"MST {mst} không hợp lệ")
        if mst and self._repo.get_by_mst(company_id, mst) is not None:
            raise DuplicateMstError(f"MST {mst} đã tồn tại")
        p = Party(
            company_id=company_id,
            code=code,
            name=name,
            mst=mst,
            address=address,
            phone=phone,
            email=email,
            is_customer=is_customer,
            is_supplier=is_supplier,
            is_employee=is_employee,
        )
        p.checksum = p.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        saved = self._repo.create_party(p)
        if self._audit:
            self._audit.append(
                entity_type="party",
                entity_id=p.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved  # type: ignore[no-any-return]

    def list_parties(self, company_id: UUID, role: str | None = None) -> list[Party]:
        return self._repo.list_parties(company_id, role)  # type: ignore[no-any-return]

    def get_party(self, pid: UUID) -> Party | None:
        return self._repo.get_party(pid)  # type: ignore[no-any-return]

    def create_department(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        parent_id: UUID | None = None,
        manager_id: UUID | None = None,
        actor: UUID,
        reason: str,
    ) -> Department:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        d = Department(
            company_id=company_id, code=code, name=name, parent_id=parent_id, manager_id=manager_id
        )
        saved = self._repo.create_department(d)
        if self._audit:
            self._audit.append(
                entity_type="department",
                entity_id=d.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved  # type: ignore[no-any-return]

    def list_departments(self, company_id: UUID) -> list[Department]:
        return self._repo.list_departments(company_id)  # type: ignore[no-any-return]
