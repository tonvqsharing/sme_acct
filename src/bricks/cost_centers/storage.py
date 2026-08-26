"""Cost centers storage adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal  # noqa: F401
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.cost_centers.contract import CostCenterRepositoryPort
from src.bricks.cost_centers.domain import CostCenter, CostCenterStatus


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
