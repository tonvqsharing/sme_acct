"""Cost center & dimension services — CRUD + lifecycle per specs §2."""

from __future__ import annotations

from uuid import UUID

from src.bricks.cost_centers.contract import (
    CostCenterRepositoryPort,
    DimensionRepositoryPort,
    DimensionValueRepositoryPort,
)
from src.bricks.cost_centers.domain import (
    GENESIS_CHECKSUM,
    CostCenter,
    CostCenterStatus,
    Dimension,
    DimensionType,
    DimensionValue,
    DimensionValueStatus,
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
    def __init__(self, repo: CostCenterRepositoryPort) -> None:
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


# ---------------------------------------------------------------------------
# DimensionService — per specs §2.1.2
# ---------------------------------------------------------------------------


class DimensionService:
    def __init__(self, repo: DimensionRepositoryPort) -> None:
        self._repo = repo

    def create(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        dimension_type: DimensionType,
        actor: UUID | None = None,
        reason: str = "",
        description: str | None = None,
        is_system: bool = False,
    ) -> Dimension:
        a = _require(actor)
        if self._repo.exists_duplicate(company_id, code):
            raise DuplicateCodeError(f"Trùng mã: {code}")
        dim = Dimension(
            company_id=company_id,
            code=(code or "").strip(),
            name=name.strip(),
            type=dimension_type,
            is_system=is_system,
            description=description,
            created_by=a,
        )
        dim.audit_checksum = _stamp_dim(dim, "CREATE", a, reason)
        return self._repo.create(dim)

    def get(self, did: UUID) -> Dimension | None:
        return self._repo.get_by_id(did)

    def list_by_company(
        self, cid: UUID, *, dimension_type: str | None = None, is_system: bool | None = None
    ) -> list[Dimension]:
        return self._repo.get_by_company(cid, dimension_type=dimension_type, is_system=is_system)

    def modify(self, did: UUID, *, new_name: str, actor: UUID, reason: str = "") -> Dimension:
        a = _require(actor)
        dim = self._get_or_404(did)
        if not dim.can_modify:
            raise InvalidTransitionError("Hệ thống dimension không thể sửa")
        dim.name = new_name.strip()
        dim.audit_checksum = _stamp_dim(dim, "MODIFY", a, reason)
        return self._repo.update(dim)

    def set_system(self, did: UUID, *, actor: UUID, reason: str = "") -> Dimension:
        a = _require(actor)
        dim = self._get_or_404(did)
        dim.is_system = True
        dim.audit_checksum = _stamp_dim(dim, "SET_SYSTEM", a, reason)
        return self._repo.update(dim)

    def _get_or_404(self, did: UUID) -> Dimension:
        found: Dimension | None = self._repo.get_by_id(did)
        if found is None:
            raise NotFoundError(f"Không tìm thấy dimension {did}")
        return found


# ---------------------------------------------------------------------------
# DimensionValueService — per specs §2.1.3
# ---------------------------------------------------------------------------


class DimensionValueService:
    def __init__(self, repo: DimensionValueRepositoryPort) -> None:
        self._repo = repo

    def create(
        self,
        *,
        company_id: UUID,
        dimension_id: UUID,
        code: str,
        name: str,
        actor: UUID | None = None,
        reason: str = "",
        description: str | None = None,
    ) -> DimensionValue:
        a = _require(actor)
        if self._repo.exists_duplicate(dimension_id, company_id, code):
            raise DuplicateCodeError(f"Trùng mã: {code}")
        dv = DimensionValue(
            company_id=company_id,
            dimension_id=dimension_id,
            code=(code or "").strip(),
            name=name.strip(),
            description=description,
            created_by=a,
        )
        dv.audit_checksum = _stamp_dv(dv, "CREATE", a, reason)
        return self._repo.create(dv)

    def get(self, dvid: UUID) -> DimensionValue | None:
        return self._repo.get_by_id(dvid)

    def list_by_company(
        self, cid: UUID, *, dimension_id: UUID | None = None, status: str | None = None
    ) -> list[DimensionValue]:
        return self._repo.get_by_company(cid, dimension_id=dimension_id, status=status)

    def deactivate(self, dvid: UUID, *, actor: UUID, reason: str = "") -> DimensionValue:
        a = _require(actor)
        dv = self._get_or_404(dvid)
        if not dv.can_modify:
            raise InvalidTransitionError("Dimension value đã INACTIVE")
        dv.status = DimensionValueStatus.INACTIVE
        dv.audit_checksum = _stamp_dv(dv, "DEACTIVATE", a, reason)
        return self._repo.update(dv)

    def reactivate(self, dvid: UUID, *, actor: UUID, reason: str = "") -> DimensionValue:
        a = _require(actor)
        dv = self._get_or_404(dvid)
        if dv.status == DimensionValueStatus.ACTIVE:
            raise InvalidTransitionError("Dimension value đã ACTIVE")
        dv.status = DimensionValueStatus.ACTIVE
        dv.audit_checksum = _stamp_dv(dv, "REACTIVATE", a, reason)
        return self._repo.update(dv)

    def modify(self, dvid: UUID, *, new_name: str, actor: UUID, reason: str = "") -> DimensionValue:
        a = _require(actor)
        dv = self._get_or_404(dvid)
        if not dv.can_modify:
            raise InvalidTransitionError("Dimension value đã INACTIVE")
        dv.name = new_name.strip()
        dv.audit_checksum = _stamp_dv(dv, "MODIFY", a, reason)
        return self._repo.update(dv)

    def _get_or_404(self, dvid: UUID) -> DimensionValue:
        found: DimensionValue | None = self._repo.get_by_id(dvid)
        if found is None:
            raise NotFoundError(f"Không tìm thấy dimension value {dvid}")
        return found


# ---------------------------------------------------------------------------
# Checksum helpers
# ---------------------------------------------------------------------------


def _stamp_dim(dim: Dimension, action: str, actor: UUID, reason: str) -> str:
    prev = dim.audit_checksum or GENESIS_CHECKSUM
    return dim.compute_checksum(prev, actor, action, reason)


def _stamp_dv(dv: DimensionValue, action: str, actor: UUID, reason: str) -> str:
    prev = dv.audit_checksum or GENESIS_CHECKSUM
    return dv.compute_checksum(prev, actor, action, reason)
