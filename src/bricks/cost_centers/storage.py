"""Cost centers & dimensions storage adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal  # noqa: F401
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.cost_centers.contract import (
    CostCenterRepositoryPort,
    DimensionRepositoryPort,
    DimensionValueRepositoryPort,
)
from src.bricks.cost_centers.domain import (
    CostCenter,
    CostCenterStatus,
    Dimension,
    DimensionType,
    DimensionValue,
    DimensionValueStatus,
)


class Base(DeclarativeBase):
    pass


class CostCenterModel(Base):
    __tablename__ = "cost_centers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="Active")
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    audit_checksum: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class SQLAlchemyCostCenterRepository(CostCenterRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: CostCenterModel) -> CostCenter:
        return CostCenter(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            status=CostCenterStatus(m.status),
            parent_id=UUID(m.parent_id) if m.parent_id else None,
            description=m.description,
            created_by=UUID(m.created_by) if m.created_by else None,
            created_at=m.created_at,
            audit_checksum=m.audit_checksum,
        )

    def create(self, cc: CostCenter) -> CostCenter:
        self._session.add(
            CostCenterModel(
                id=str(cc.id),
                company_id=str(cc.company_id),
                code=cc.code,
                name=cc.name,
                status=cc.status.value,
                parent_id=str(cc.parent_id) if cc.parent_id else None,
                description=cc.description,
                created_by=str(cc.created_by) if cc.created_by else None,
                audit_checksum=cc.audit_checksum,
                created_at=cc.created_at,
            )
        )
        self._session.commit()
        return cc

    def get_by_id(self, cid: UUID) -> CostCenter | None:
        m = self._session.get(CostCenterModel, str(cid))
        return self._to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[CostCenter]:
        rows = (
            self._session.query(CostCenterModel)
            .filter(CostCenterModel.company_id == str(cid))
            .order_by(CostCenterModel.code.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def update(self, cc: CostCenter) -> CostCenter:
        m = self._session.get(CostCenterModel, str(cc.id))
        if m is None:
            raise ValueError("not found")
        m.name = cc.name
        m.status = cc.status.value
        m.audit_checksum = cc.audit_checksum
        self._session.commit()
        return cc

    def exists_duplicate(self, cid: UUID, code: str) -> bool:
        row = (
            self._session.query(CostCenterModel.id)
            .filter(
                CostCenterModel.company_id == str(cid),
                CostCenterModel.code == code,
            )
            .first()
        )
        return row is not None


# ---------------------------------------------------------------------------
# Dimension model + repository — per specs §3.1.2
# ---------------------------------------------------------------------------


class DimensionModel(Base):
    __tablename__ = "dimensions"
    __table_args__ = (UniqueConstraint("code", "company_id", name="uq_dimensions_code_company"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20), index=True)
    is_system: Mapped[bool] = mapped_column(default=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    audit_checksum: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class SQLAlchemyDimensionRepository(DimensionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: DimensionModel) -> Dimension:
        return Dimension(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            type=DimensionType(m.type),
            is_system=m.is_system,
            description=m.description,
            created_by=UUID(m.created_by) if m.created_by else None,
            created_at=m.created_at,
            audit_checksum=m.audit_checksum,
        )

    def create(self, dim: Dimension) -> Dimension:
        self._session.add(
            DimensionModel(
                id=str(dim.id),
                company_id=str(dim.company_id),
                code=dim.code,
                name=dim.name,
                type=dim.type.value,
                is_system=dim.is_system,
                description=dim.description,
                created_by=str(dim.created_by) if dim.created_by else None,
                audit_checksum=dim.audit_checksum,
                created_at=dim.created_at,
            )
        )
        self._session.commit()
        return dim

    def get_by_id(self, did: UUID) -> Dimension | None:
        m = self._session.get(DimensionModel, str(did))
        return self._to_domain(m) if m else None

    def get_by_company(
        self, cid: UUID, *, dimension_type: str | None = None, is_system: bool | None = None
    ) -> list[Dimension]:
        q = self._session.query(DimensionModel).filter(DimensionModel.company_id == str(cid))
        if dimension_type is not None:
            q = q.filter(DimensionModel.type == dimension_type)
        if is_system is not None:
            q = q.filter(DimensionModel.is_system == is_system)
        return [self._to_domain(r) for r in q.order_by(DimensionModel.code).all()]

    def update(self, dim: Dimension) -> Dimension:
        m = self._session.get(DimensionModel, str(dim.id))
        if m is None:
            raise ValueError("not found")
        m.name = dim.name
        m.description = dim.description
        m.is_system = dim.is_system
        m.audit_checksum = dim.audit_checksum
        self._session.commit()
        return dim

    def exists_duplicate(self, cid: UUID, code: str) -> bool:
        row = (
            self._session.query(DimensionModel.id)
            .filter(
                DimensionModel.company_id == str(cid),
                DimensionModel.code == code,
            )
            .first()
        )
        return row is not None


# ---------------------------------------------------------------------------
# DimensionValue model + repository — per specs §3.1.3
# ---------------------------------------------------------------------------


class DimensionValueModel(Base):
    __tablename__ = "dimension_values"
    __table_args__ = (
        UniqueConstraint(
            "code",
            "dimension_id",
            "company_id",
            name="uq_dimension_values_code_dim_company",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    dimension_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="Active", index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    audit_checksum: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class SQLAlchemyDimensionValueRepository(DimensionValueRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: DimensionValueModel) -> DimensionValue:
        return DimensionValue(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            dimension_id=UUID(m.dimension_id),
            code=m.code,
            name=m.name,
            status=DimensionValueStatus(m.status),
            description=m.description,
            created_by=UUID(m.created_by) if m.created_by else None,
            created_at=m.created_at,
            audit_checksum=m.audit_checksum,
        )

    def create(self, dv: DimensionValue) -> DimensionValue:
        self._session.add(
            DimensionValueModel(
                id=str(dv.id),
                company_id=str(dv.company_id),
                dimension_id=str(dv.dimension_id),
                code=dv.code,
                name=dv.name,
                status=dv.status.value,
                description=dv.description,
                created_by=str(dv.created_by) if dv.created_by else None,
                audit_checksum=dv.audit_checksum,
                created_at=dv.created_at,
            )
        )
        self._session.commit()
        return dv

    def get_by_id(self, dvid: UUID) -> DimensionValue | None:
        m = self._session.get(DimensionValueModel, str(dvid))
        return self._to_domain(m) if m else None

    def get_by_company(
        self, cid: UUID, *, dimension_id: UUID | None = None, status: str | None = None
    ) -> list[DimensionValue]:
        q = self._session.query(DimensionValueModel).filter(
            DimensionValueModel.company_id == str(cid)
        )
        if dimension_id is not None:
            q = q.filter(DimensionValueModel.dimension_id == str(dimension_id))
        if status is not None:
            q = q.filter(DimensionValueModel.status == status)
        return [self._to_domain(r) for r in q.order_by(DimensionValueModel.code).all()]

    def update(self, dv: DimensionValue) -> DimensionValue:
        m = self._session.get(DimensionValueModel, str(dv.id))
        if m is None:
            raise ValueError("not found")
        m.name = dv.name
        m.description = dv.description
        m.status = dv.status.value
        m.audit_checksum = dv.audit_checksum
        self._session.commit()
        return dv

    def exists_duplicate(self, dim_id: UUID, cid: UUID, code: str) -> bool:
        row = (
            self._session.query(DimensionValueModel.id)
            .filter(
                DimensionValueModel.dimension_id == str(dim_id),
                DimensionValueModel.company_id == str(cid),
                DimensionValueModel.code == code,
            )
            .first()
        )
        return row is not None
