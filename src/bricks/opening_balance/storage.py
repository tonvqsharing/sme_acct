"""Opening balance storage — SQLAlchemy adapter."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.opening_balance.domain import (
    BankOpening,
    CounterpartyBalance,
    GLBalance,
    OpeningBatch,
)


class Base(DeclarativeBase):
    pass


class OpeningBatchModel(Base):
    __tablename__ = "opening_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    fiscal_year_id: Mapped[str] = mapped_column(String(36), index=True)
    source: Mapped[str] = mapped_column(String(20))
    state: Mapped[str] = mapped_column(String(20), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


class OpeningGLModel(Base):
    __tablename__ = "opening_gl"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    account_code: Mapped[str] = mapped_column(String(20))
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default="VND")


class OpeningBankModel(Base):
    __tablename__ = "opening_bank"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    bank_account_id: Mapped[str] = mapped_column(String(36))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))


class OpeningCounterpartyModel(Base):
    __tablename__ = "opening_counterparty"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(36), index=True)
    account_code: Mapped[str] = mapped_column(String(20))
    party_id: Mapped[str] = mapped_column(String(36), index=True)
    side: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    proof: Mapped[bool] = mapped_column(Boolean, default=False)


class SQLAlchemyOpeningBalanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_batch(m: OpeningBatchModel) -> OpeningBatch:
        from src.bricks.opening_balance.domain import BatchSource, BatchState

        return OpeningBatch(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            fiscal_year_id=UUID(m.fiscal_year_id),
            source=BatchSource(m.source),
            state=BatchState(m.state),
            checksum=m.checksum,
        )

    def create_batch(self, b: OpeningBatch) -> OpeningBatch:
        self._session.add(
            OpeningBatchModel(
                id=str(b.id),
                company_id=str(b.company_id),
                fiscal_year_id=str(b.fiscal_year_id),
                source=b.source.value,
                state=b.state.value,
                checksum=b.checksum,
            )
        )
        self._session.commit()
        return b

    def get_batch(self, bid: UUID) -> OpeningBatch | None:
        m = self._session.get(OpeningBatchModel, str(bid))
        return self._to_batch(m) if m else None

    def update_batch(self, b: OpeningBatch) -> OpeningBatch:
        m = self._session.get(OpeningBatchModel, str(b.id))
        if m is None:
            raise ValueError("not found")
        m.state = b.state.value
        m.checksum = b.checksum
        self._session.commit()
        return b

    def list_batches(self, company_id: UUID) -> list[OpeningBatch]:
        rows = (
            self._session.query(OpeningBatchModel)
            .filter(OpeningBatchModel.company_id == str(company_id))
            .all()
        )
        return [self._to_batch(r) for r in rows]

    def add_gl(self, row: GLBalance) -> GLBalance:
        self._session.add(
            OpeningGLModel(
                id=str(row.id),
                batch_id=str(row.batch_id),
                account_code=row.account_code,
                debit=row.debit,
                credit=row.credit,
                currency_code=row.currency_code,
            )
        )
        self._session.commit()
        return row

    def list_gl(self, batch_id: UUID) -> list[GLBalance]:
        rows = (
            self._session.query(OpeningGLModel)
            .filter(OpeningGLModel.batch_id == str(batch_id))
            .all()
        )
        return [
            GLBalance(
                id=UUID(r.id),
                batch_id=UUID(r.batch_id),
                account_code=r.account_code,
                debit=Decimal(str(r.debit)),
                credit=Decimal(str(r.credit)),
                currency_code=r.currency_code,
            )
            for r in rows
        ]

    def add_bank(self, row: BankOpening) -> BankOpening:
        self._session.add(
            OpeningBankModel(
                id=str(row.id),
                batch_id=str(row.batch_id),
                bank_account_id=str(row.bank_account_id),
                amount=row.amount,
            )
        )
        self._session.commit()
        return row

    def list_bank(self, batch_id: UUID) -> list[BankOpening]:
        rows = (
            self._session.query(OpeningBankModel)
            .filter(OpeningBankModel.batch_id == str(batch_id))
            .all()
        )
        return [
            BankOpening(
                id=UUID(r.id),
                batch_id=UUID(r.batch_id),
                bank_account_id=UUID(r.bank_account_id),
                amount=Decimal(str(r.amount)),
            )
            for r in rows
        ]

    def add_counterparty(self, row: CounterpartyBalance) -> CounterpartyBalance:
        self._session.add(
            OpeningCounterpartyModel(
                id=str(row.id),
                batch_id=str(row.batch_id),
                account_code=row.account_code,
                party_id=str(row.party_id),
                side=row.side,
                amount=row.amount,
                proof=row.proof,
            )
        )
        self._session.commit()
        return row

    def list_counterparty(self, batch_id: UUID) -> list[CounterpartyBalance]:
        rows = (
            self._session.query(OpeningCounterpartyModel)
            .filter(OpeningCounterpartyModel.batch_id == str(batch_id))
            .all()
        )
        return [
            CounterpartyBalance(
                id=UUID(r.id),
                batch_id=UUID(r.batch_id),
                account_code=r.account_code,
                party_id=UUID(r.party_id),
                side=r.side,
                amount=Decimal(str(r.amount)),
                proof=r.proof,
            )
            for r in rows
        ]
