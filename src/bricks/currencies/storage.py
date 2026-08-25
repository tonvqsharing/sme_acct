"""Currencies storage — currencies + exchange_rates tables."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.currencies.domain import Currency


class Base(DeclarativeBase):
    pass


class CurrencyModel(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(10))
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    is_base: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SQLAlchemyCurrencyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, c: Currency) -> Currency:
        self._session.add(
            CurrencyModel(
                code=c.code,
                name=c.name,
                symbol=c.symbol,
                decimal_places=c.decimal_places,
                is_base=c.is_base,
                is_active=c.is_active,
            )
        )
        self._session.commit()
        return c

    def get_by_code(self, code: str) -> Currency | None:
        m = self._session.get(CurrencyModel, code)
        return (
            Currency(
                code=m.code,
                name=m.name,
                symbol=m.symbol,
                decimal_places=m.decimal_places,
                is_base=m.is_base,
                is_active=m.is_active,
            )
            if m
            else None
        )

    def all(self) -> list[Currency]:
        rows = self._session.query(CurrencyModel).all()
        return [
            Currency(
                code=r.code,
                name=r.name,
                symbol=r.symbol,
                decimal_places=r.decimal_places,
                is_base=r.is_base,
                is_active=r.is_active,
            )
            for r in rows
        ]

    def update(self, c: Currency) -> Currency:
        m = self._session.get(CurrencyModel, c.code)
        if m is None:
            raise ValueError("not found")
        m.is_active = c.is_active
        m.name = c.name
        self._session.commit()
        return c

    def count_transactions_for(self, code: str) -> int:
        return 0  # v1: no transaction linkage yet


class ExchangeRateModel(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    currency_code: Mapped[str] = mapped_column(String(3), index=True)
    rate_type: Mapped[str] = mapped_column(String(10), index=True)
    rate_date: Mapped[date] = mapped_column(Date, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    source: Mapped[str] = mapped_column(String(12))
    actor: Mapped[str] = mapped_column(String(36))


class SQLAlchemyExchangeRateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, r: Any) -> Any:
        from src.bricks.currencies.domain import ExchangeRate as _E

        assert isinstance(r, _E)
        self._session.add(
            ExchangeRateModel(
                currency_code=r.currency_code,
                rate_type=r.rate_type.value,
                rate_date=r.rate_date,
                rate=r.rate,
                source=r.source.value,
                actor=str(r.actor),
            )
        )
        self._session.commit()
        return r

    def latest_on_or_before(self, code: str, rate_type: Any, on_date: date) -> Any | None:

        from src.bricks.currencies.domain import ExchangeRate as _E

        row = (
            self._session.query(ExchangeRateModel)
            .filter(
                ExchangeRateModel.currency_code == code,
                ExchangeRateModel.rate_type == getattr(rate_type, "value", rate_type),
                ExchangeRateModel.rate_date <= on_date,
            )
            .order_by(ExchangeRateModel.rate_date.desc())
            .first()
        )
        if row is None:
            return None
        return _E(
            currency_code=row.currency_code,
            rate_type=rate_type.__class__ and rate_type,
            rate_date=row.rate_date,
            rate=Decimal(str(row.rate)),
            source=__import__(
                "src.bricks.currencies.domain", fromlist=["FxRateSource"]
            ).FxRateSource(row.source),
            actor=uuid4(),
        )


class RevaluationRunModel(Base):
    __tablename__ = "revaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    rate_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), index=True, default="DRAFT")
    entries: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    reversal_entries: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64), default="")
    approver: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SQLAlchemyRevaluationRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, run: Any) -> Any:
        self._session.add(
            RevaluationRunModel(
                id=str(run.id),
                company_id=str(run.company_id),
                period_start=run.period_start,
                period_end=run.period_end,
                rate_date=run.rate_date,
                status=run.status.value,
                entries=[
                    {
                        "account_code": e.account_code,
                        "currency_code": e.currency_code,
                        "balance_original": str(e.balance_original),
                        "rate_applied": str(e.rate_applied),
                        "old_vnd": str(e.old_vnd),
                        "new_vnd": str(e.new_vnd),
                    }
                    for e in run.entries
                ],
                reversal_entries=[],
                checksum=run.checksum,
                approver=str(run.approver) if run.approver else None,
            )
        )
        self._session.commit()
        return run

    def update(self, run: Any) -> Any:
        m = (
            self._session.query(RevaluationRunModel)
            .filter(RevaluationRunModel.id == str(run.id))
            .first()
        )
        if m is None:
            raise ValueError("not found")
        m.status = run.status.value
        m.checksum = run.checksum
        m.approver = str(run.approver) if run.approver else None
        self._session.commit()
        return run

    def find_posted_overlap(self, cid: str, start: date, end: date) -> Any | None:
        row = (
            self._session.query(RevaluationRunModel)
            .filter(
                RevaluationRunModel.company_id == str(cid),
                RevaluationRunModel.status == "POSTED",
            )
            .first()
        )
        return row  # caller only needs truthiness + entries via domain rebuild

    # minimal domain round-trip helpers used by service flows
    def rows_get(self, rid: str) -> Any:
        row = (
            self._session.query(RevaluationRunModel)
            .filter(RevaluationRunModel.id == str(rid))
            .first()
        )
        if row is None:
            from src.bricks.bank_cash.services import NotFoundError

            raise NotFoundError("Không tìm thấy reval run")
        from src.bricks.currencies.domain import (
            RevaluationEntry,
            RevaluationRun,
            RevaluationStatus,
        )

        entries = [
            RevaluationEntry(
                account_code=d["account_code"],
                currency_code=d["currency_code"],
                balance_original=Decimal(d["balance_original"]),
                rate_applied=Decimal(d["rate_applied"]),
                old_vnd=Decimal(d["old_vnd"]),
                new_vnd=Decimal(d["new_vnd"]),
            )
            for d in row.entries
        ]
        rev_entries = [
            RevaluationEntry(
                account_code=d["account_code"],
                currency_code=d["currency_code"],
                balance_original=Decimal(d["balance_original"]),
                rate_applied=Decimal(d["rate_applied"]),
                old_vnd=Decimal(d["old_vnd"]),
                new_vnd=Decimal(d["new_vnd"]),
            )
            for d in row.reversal_entries
        ]
        return RevaluationRun(
            id=UUID(row.id),
            company_id=UUID(row.company_id),
            period_start=row.period_start,
            period_end=row.period_end,
            rate_date=row.rate_date,
            entries=entries,
            reversal_entries=rev_entries,
            status=RevaluationStatus(row.status),
            checksum=row.checksum,
            approver=UUID(row.approver) if row.approver else None,
        )

    get_by_id = rows_get
