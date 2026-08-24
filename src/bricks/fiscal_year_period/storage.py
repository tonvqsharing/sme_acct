"""Fiscal year storage — re-exports domain models + SQLAlchemy adapters."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.fiscal_year_period.domain import (
    FiscalYear,
    FiscalYearStatus,
    Period,
    PeriodStatus,
)


class Base(DeclarativeBase):
    pass


class FiscalYearModel(Base):
    __tablename__ = "fiscal_years"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class PeriodModel(Base):
    __tablename__ = "fiscal_periods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fiscal_year_id: Mapped[str] = mapped_column(String(36), index=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    locked_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lock_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SQLAlchemyFiscalYearRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, fy: FiscalYear) -> FiscalYear:
        self._session.add(
            FiscalYearModel(
                id=str(fy.id),
                company_id=str(fy.company_id),
                name=fy.name,
                start_date=fy.start_date,
                end_date=fy.end_date,
                status=fy.status.value,
                created_by=str(fy.created_by) if fy.created_by else None,
            )
        )
        self._session.commit()
        return fy

    def get_by_id(self, fy_id: UUID) -> FiscalYear | None:
        m = self._session.get(FiscalYearModel, str(fy_id))
        return self._to_domain(m) if m else None

    @staticmethod
    def _to_domain(m: FiscalYearModel) -> FiscalYear:
        return FiscalYear(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            name=m.name,
            start_date=m.start_date,
            end_date=m.end_date,
            status=FiscalYearStatus(m.status),
            created_by=UUID(m.created_by) if m.created_by else None,
        )

    def get_by_company(self, company_id: UUID) -> list[FiscalYear]:
        rows = (
            self._session.query(FiscalYearModel)
            .filter(FiscalYearModel.company_id == str(company_id))
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def update(self, fy: FiscalYear) -> FiscalYear:
        m = self._session.get(FiscalYearModel, str(fy.id))
        if m is None:
            raise ValueError(f"FiscalYear {fy.id} not found")
        m.status = fy.status.value
        self._session.commit()
        return fy


class SQLAlchemyPeriodRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_many(self, periods: list[Period]) -> list[Period]:
        for p in periods:
            self._session.add(
                PeriodModel(
                    id=str(p.id),
                    fiscal_year_id=str(p.fiscal_year_id),
                    company_id=str(p.company_id),
                    sequence=p.sequence,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    status=p.status.value,
                )
            )
        self._session.commit()
        return list(periods)

    def get_by_id(self, period_id: UUID) -> Period | None:
        m = self._session.get(PeriodModel, str(period_id))
        return self._to_domain(m) if m else None

    @staticmethod
    def _to_domain(m: PeriodModel) -> Period:
        return Period(
            id=UUID(m.id),
            fiscal_year_id=UUID(m.fiscal_year_id),
            company_id=UUID(m.company_id),
            sequence=m.sequence,
            start_date=m.start_date,
            end_date=m.end_date,
            status=PeriodStatus(m.status),
            locked_by=UUID(m.locked_by) if m.locked_by else None,
            lock_reason=m.lock_reason,
        )

    def get_by_year(self, fiscal_year_id: UUID) -> list[Period]:
        rows = (
            self._session.query(PeriodModel)
            .filter(PeriodModel.fiscal_year_id == str(fiscal_year_id))
            .order_by(PeriodModel.sequence.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def find_by_date(self, company_id: UUID, on_date: date) -> Period | None:
        row = (
            self._session.query(PeriodModel)
            .filter(
                PeriodModel.company_id == str(company_id),
                PeriodModel.start_date <= on_date,
                PeriodModel.end_date >= on_date,
            )
            .first()
        )
        return self._to_domain(row) if row else None

    def update(self, period: Period) -> Period:
        m = self._session.get(PeriodModel, str(period.id))
        if m is None:
            raise ValueError(f"Period {period.id} not found")
        m.status = period.status.value
        m.locked_by = str(period.locked_by) if period.locked_by else None
        m.lock_reason = period.lock_reason
        self._session.commit()
        return period
