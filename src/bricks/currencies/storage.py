"""Currencies storage — currencies + exchange_rates tables."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

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
