"""Cost center service — CRUD + lifecycle per specs §2."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.bricks.cost_centers.domain import (
    GENESIS_CHECKSUM,
    CostCenter,
    CostCenterStatus,
)


class DuplicateCodeError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidTransitionError(ValueError):
    pass


def _require(actor: UUID | None) -> UUID:
    if actor is None:
        raise ValueError("actor là bắt buộc")
    return actor


def _stamp(cc: CostCenter, action: str, actor: UUID, reason: str) -> str:
    prev = cc.audit_checksum or GENESIS_CHECKSUM
    return cc.compute_checksum(prev, actor, action, reason)


class CostCenterService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def create(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        actor: UUID | None = None,
        reason: str = "",
        description: str | None = None,
        parent_id: UUID | None = None,
    ) -> CostCenter:
        a = _require(actor)
        if self._repo.exists_duplicate(company_id, code):
            raise DuplicateCodeError(f"Trùng mã: {code}")
        cc = CostCenter(
            company_id=company_id,
            code=(code or "").strip(),
            name=name.strip(),
            parent_id=parent_id,
            description=description,
            created_by=a,
        )
        cc.audit_checksum = _stamp(cc, "CREATE", a, reason)
        created: CostCenter = self._repo.create(cc)
        return created

    def get(self, cid: UUID) -> CostCenter | None:
        found: CostCenter | None = self._repo.get_by_id(cid)
        return found

    def list_by_company(self, cid: UUID) -> list[CostCenter]:
        rows: list[CostCenter] = self._repo.get_by_company(cid)
        return rows

    def deactivate(self, cid: UUID, *, actor: UUID, reason: str = "") -> CostCenter:
        a = _require(actor)
        cc = self._get_or_404(cid)
        if not cc.can_modify:
            raise InvalidTransitionError("Chỉ TSCĐ ACTIVE mới được vô hiệu hóa")
        cc.status = CostCenterStatus.INACTIVE
        cc.audit_checksum = _stamp(cc, "DEACTIVATE", a, reason)
        saved: CostCenter = self._repo.update(cc)
        return saved

    def reactivate(self, cid: UUID, *, actor: UUID, reason: str = "") -> CostCenter:
        a = _require(actor)
        cc = self._get_or_404(cid)
        if cc.status == CostCenterStatus.CLOSED:
            raise InvalidTransitionError("TSCĐ đã đóng không thể mở lại")
        cc.status = CostCenterStatus.ACTIVE
        cc.audit_checksum = _stamp(cc, "REACTIVATE", a, reason)
        saved: CostCenter = self._repo.update(cc)
        return saved

    def close(self, cid: UUID, *, actor: UUID, reason: str = "") -> CostCenter:
        a = _require(actor)
        cc = self._get_or_404(cid)
        cc.status = CostCenterStatus.CLOSED
        cc.audit_checksum = _stamp(cc, "CLOSE", a, reason)
        saved: CostCenter = self._repo.update(cc)
        return saved

    def modify(self, cid: UUID, *, new_name: str, actor: UUID, reason: str = "") -> CostCenter:
        a = _require(actor)
        cc = self._get_or_404(cid)
        if not cc.can_modify:
            raise InvalidTransitionError("Chỉ TSCĐ ACTIVE mới được sửa")
        cc.name = new_name.strip()
        cc.audit_checksum = _stamp(cc, "MODIFY", a, reason)
        saved: CostCenter = self._repo.update(cc)
        return saved

    def _get_or_404(self, cid: UUID) -> CostCenter:
        found: CostCenter | None = self._repo.get_by_id(cid)
        if found is None:
            raise NotFoundError(f"Không tìm thấy trung tâm chi phí {cid}")
        return found
