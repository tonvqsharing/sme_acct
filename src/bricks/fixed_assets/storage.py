"""Fixed assets storage adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.fixed_assets.contract import FixedAssetRepositoryPort
from src.bricks.fixed_assets.domain import FixedAsset


class Base(DeclarativeBase):
    pass


class FixedAssetModel(Base):
    __tablename__ = "fixed_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    asset_code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20), default="huu_hinh")
    original_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    acquisition_date: Mapped[date] = mapped_column(Date)
    useful_life_months: Mapped[int] = mapped_column(Integer)
    depreciation_account: Mapped[str] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    accumulated_depreciation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    checksum: Mapped[str] = mapped_column(String(64), default="")


class SQLAlchemyFixedAssetRepository(FixedAssetRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: FixedAssetModel) -> FixedAsset:
        from decimal import Decimal as D

        return FixedAsset(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            asset_code=m.asset_code,
            name=m.name,
            category=m.category,
            original_cost=D(str(m.original_cost)),
            acquisition_date=m.acquisition_date,
            useful_life_months=m.useful_life_months,
            depreciation_account=m.depreciation_account,
            is_active=m.is_active,
            accumulated_depreciation=D(str(m.accumulated_depreciation)),
            checksum=m.checksum,
        )

    def create(self, a: FixedAsset) -> FixedAsset:
        self._session.add(
            FixedAssetModel(
                id=str(a.id),
                company_id=str(a.company_id),
                asset_code=a.asset_code,
                name=a.name,
                category=a.category,
                original_cost=a.original_cost,
                acquisition_date=a.acquisition_date,
                useful_life_months=a.useful_life_months,
                depreciation_account=a.depreciation_account,
                is_active=a.is_active,
                accumulated_depreciation=a.accumulated_depreciation,
                checksum=a.checksum,
            )
        )
        self._session.commit()
        return a

    def get_by_id(self, aid: UUID) -> FixedAsset | None:
        m = self._session.get(FixedAssetModel, str(aid))
        return self._to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[FixedAsset]:
        rows = (
            self._session.query(FixedAssetModel)
            .filter(FixedAssetModel.company_id == str(cid))
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def update(self, a: FixedAsset) -> FixedAsset:
        m = self._session.get(FixedAssetModel, str(a.id))
        if m is None:
            raise ValueError("not found")
        # Full-field projection — prevents silent field drops when domain
        # surface grows. All mutable fields written explicitly.
        m.name = a.name
        m.category = a.category
        m.original_cost = a.original_cost
        m.useful_life_months = a.useful_life_months
        m.depreciation_account = a.depreciation_account
        m.is_active = a.is_active
        m.accumulated_depreciation = a.accumulated_depreciation
        m.checksum = a.checksum
        self._session.commit()
        return a

    def exists_duplicate(self, cid: UUID, code: str) -> bool:
        row = (
            self._session.query(FixedAssetModel.id)
            .filter(
                FixedAssetModel.company_id == str(cid),
                FixedAssetModel.asset_code == code,
            )
            .first()
        )
        return row is not None

    def find_active_with_remaining(self, cid: UUID) -> list[FixedAsset]:
        return [
            a
            for a in self.get_by_company(cid)
            if a.is_active and a.accumulated_depreciation < a.original_cost
        ]
