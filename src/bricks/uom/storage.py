"""UOM storage."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.uom.domain import UOM


class Base(DeclarativeBase):
    pass


class UOMModel(Base):
    __tablename__ = "uoms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    factor: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1)
    base_uom_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    checksum: Mapped[str] = mapped_column(String(64), default="")


class SQLAlchemyUOMRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: UOMModel) -> UOM:
        return UOM(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            factor=Decimal(str(m.factor)),
            base_uom_id=UUID(m.base_uom_id) if m.base_uom_id else None,
            active=m.active,
            checksum=m.checksum,
        )

    def create_uom(self, u: UOM) -> UOM:
        self._session.add(
            UOMModel(
                id=str(u.id),
                company_id=str(u.company_id),
                code=u.code,
                name=u.name,
                factor=u.factor,
                base_uom_id=str(u.base_uom_id) if u.base_uom_id else None,
                active=u.active,
                checksum=u.checksum,
            )
        )
        self._session.commit()
        return u

    def get_uom(self, uid: UUID) -> UOM | None:
        m = self._session.get(UOMModel, str(uid))
        return self._to_domain(m) if m else None

    def get_by_code(self, company_id: UUID, code: str) -> UOM | None:
        row = (
            self._session.query(UOMModel)
            .filter(UOMModel.company_id == str(company_id), UOMModel.code == code)
            .first()
        )
        return self._to_domain(row) if row else None

    def list_uoms(self, company_id: UUID) -> list[UOM]:
        rows = self._session.query(UOMModel).filter(UOMModel.company_id == str(company_id)).all()
        return [self._to_domain(r) for r in rows]
