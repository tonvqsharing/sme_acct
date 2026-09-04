"""Party storage — SQLAlchemy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.party.domain import Department, Party


class Base(DeclarativeBase):
    pass


class PartyModel(Base):
    __tablename__ = "parties"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(200))
    mst: Mapped[str | None] = mapped_column(String(14), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_supplier: Mapped[bool] = mapped_column(Boolean, default=False)
    is_employee: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    checksum: Mapped[str] = mapped_column(String(64), default="")


class DepartmentModel(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SQLAlchemyPartyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_party(m: PartyModel) -> Party:
        return Party(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            mst=m.mst,
            address=m.address,
            phone=m.phone,
            email=m.email,
            is_customer=m.is_customer,
            is_supplier=m.is_supplier,
            is_employee=m.is_employee,
            active=m.active,
            checksum=m.checksum,
        )

    def create_party(self, p: Party) -> Party:
        self._session.add(
            PartyModel(
                id=str(p.id),
                company_id=str(p.company_id),
                code=p.code,
                name=p.name,
                mst=p.mst,
                address=p.address,
                phone=p.phone,
                email=p.email,
                is_customer=p.is_customer,
                is_supplier=p.is_supplier,
                is_employee=p.is_employee,
                active=p.active,
                checksum=p.checksum,
            )
        )
        self._session.commit()
        return p

    def get_party(self, pid: UUID) -> Party | None:
        m = self._session.get(PartyModel, str(pid))
        return self._to_party(m) if m else None

    def get_by_code(self, company_id: UUID, code: str) -> Party | None:
        row = (
            self._session.query(PartyModel)
            .filter(PartyModel.company_id == str(company_id), PartyModel.code == code)
            .first()
        )
        return self._to_party(row) if row else None

    def get_by_mst(self, company_id: UUID, mst: str) -> Party | None:
        if not mst:
            return None
        row = (
            self._session.query(PartyModel)
            .filter(PartyModel.company_id == str(company_id), PartyModel.mst == mst)
            .first()
        )
        return self._to_party(row) if row else None

    def list_parties(self, company_id: UUID, role: str | None = None) -> list[Party]:
        q = self._session.query(PartyModel).filter(PartyModel.company_id == str(company_id))
        if role == "customer":
            q = q.filter(PartyModel.is_customer.is_(True))
        elif role == "supplier":
            q = q.filter(PartyModel.is_supplier.is_(True))
        elif role == "employee":
            q = q.filter(PartyModel.is_employee.is_(True))
        return [self._to_party(r) for r in q.all()]

    def create_department(self, d: Department) -> Department:
        self._session.add(
            DepartmentModel(
                id=str(d.id),
                company_id=str(d.company_id),
                code=d.code,
                name=d.name,
                parent_id=str(d.parent_id) if d.parent_id else None,
                manager_id=str(d.manager_id) if d.manager_id else None,
            )
        )
        self._session.commit()
        return d

    def get_department(self, did: UUID) -> Department | None:
        m = self._session.get(DepartmentModel, str(did))
        if not m:
            return None
        return Department(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            parent_id=UUID(m.parent_id) if m.parent_id else None,
            manager_id=UUID(m.manager_id) if m.manager_id else None,
        )

    def list_departments(self, company_id: UUID) -> list[Department]:
        rows = (
            self._session.query(DepartmentModel)
            .filter(DepartmentModel.company_id == str(company_id))
            .all()
        )
        return [
            Department(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                code=r.code,
                name=r.name,
                parent_id=UUID(r.parent_id) if r.parent_id else None,
                manager_id=UUID(r.manager_id) if r.manager_id else None,
            )
            for r in rows
        ]
