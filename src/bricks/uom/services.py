"""UOM service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.uom.domain import GENESIS_CHECKSUM, UOM


class DuplicateCodeError(Exception):
    pass


class UOMService:
    def __init__(self, *, repo: Any, audit: Any | None = None) -> None:
        self._repo = repo
        self._audit = audit

    def create_uom(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        factor: Any = Decimal(1),
        base_uom_id: UUID | None = None,
        actor: UUID,
        reason: str,
    ) -> UOM:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        if self._repo.get_by_code(company_id, code) is not None:
            raise DuplicateCodeError(f"UOM {code} đã tồn tại")
        fac = Decimal(str(factor))
        if fac <= 0:
            raise ValueError("factor must be >0")
        if base_uom_id:
            base = self._repo.get_uom(base_uom_id)
            if not base or base.company_id != company_id:
                raise ValueError("base_uom not found in company")
        u = UOM(company_id=company_id, code=code, name=name, factor=fac, base_uom_id=base_uom_id)
        u.checksum = u.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        saved = self._repo.create_uom(u)
        if self._audit:
            self._audit.append(
                entity_type="uom",
                entity_id=u.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved  # type: ignore[no-any-return]

    def list_uoms(self, company_id: UUID) -> list[UOM]:
        return self._repo.list_uoms(company_id)  # type: ignore[no-any-return]
