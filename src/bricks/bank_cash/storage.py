"""Bank & cash storage adapters."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.bank_cash.contract import (
    BankAccountRepositoryPort,
    CashAccountRepositoryPort,
)
from src.bricks.bank_cash.domain import (
    BankAccount,
    BankAccountStatus,
    CashAccount,
    CashAccountStatus,
    Reconciliation,
)


class Base(DeclarativeBase):
    pass


class BankAccountModel(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    bank_name: Mapped[str] = mapped_column(String(100))
    account_number: Mapped[str] = mapped_column(String(30), index=True)
    account_holder: Mapped[str] = mapped_column(String(255))
    branch: Mapped[str] = mapped_column(String(200), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[date] = mapped_column(Date)
    checksum: Mapped[str] = mapped_column(String(64), default="")


class CashAccountModel(Base):
    __tablename__ = "cash_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[date] = mapped_column(Date)
    checksum: Mapped[str] = mapped_column(String(64), default="")


def _bank_to_domain(m: BankAccountModel) -> BankAccount:
    return BankAccount(
        id=UUID(m.id),
        company_id=UUID(m.company_id),
        bank_name=m.bank_name,
        account_number=m.account_number,
        account_holder=m.account_holder,
        branch=m.branch,
        is_primary=m.is_primary,
        status=BankAccountStatus(m.status),
        created_at=m.created_at,
        checksum=m.checksum,
    )


class SQLAlchemyBankAccountRepository(BankAccountRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, acc: BankAccount) -> BankAccount:
        self._session.add(
            BankAccountModel(
                id=str(acc.id),
                company_id=str(acc.company_id),
                bank_name=acc.bank_name,
                account_number=acc.account_number,
                account_holder=acc.account_holder,
                branch=acc.branch,
                is_primary=acc.is_primary,
                status=acc.status.value,
                created_at=acc.created_at,
                checksum=acc.checksum,
            )
        )
        self._session.commit()
        return acc

    def get_by_id(self, aid: UUID) -> BankAccount | None:
        m = self._session.get(BankAccountModel, str(aid))
        return _bank_to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[BankAccount]:
        rows = (
            self._session.query(BankAccountModel)
            .filter(BankAccountModel.company_id == str(cid))
            .all()
        )
        return [_bank_to_domain(r) for r in rows]

    def update(self, acc: BankAccount) -> BankAccount:
        m = self._session.get(BankAccountModel, str(acc.id))
        if m is None:
            raise ValueError("not found")
        m.bank_name = acc.bank_name
        m.is_primary = acc.is_primary
        m.status = acc.status.value
        m.checksum = acc.checksum
        self._session.commit()
        return acc

    def find_primary(self, cid: UUID) -> BankAccount | None:
        row = (
            self._session.query(BankAccountModel)
            .filter(
                BankAccountModel.company_id == str(cid),
                BankAccountModel.is_primary.is_(True),
            )
            .first()
        )
        return _bank_to_domain(row) if row else None

    def validate_account_number_unique(self, cid: UUID, number: str) -> bool:
        return not (
            self._session.query(BankAccountModel.id)
            .filter(
                BankAccountModel.company_id == str(cid),
                BankAccountModel.account_number == number,
            )
            .first()
        )


def _cash_to_domain(m: CashAccountModel) -> CashAccount:
    from decimal import Decimal as D

    return CashAccount(
        id=UUID(m.id),
        company_id=UUID(m.company_id),
        code=m.code,
        name=m.name,
        opening_balance=D(str(m.opening_balance)),
        current_balance=D(str(m.current_balance)),
        is_system=m.is_system,
        status=CashAccountStatus(m.status),
        created_at=m.created_at,
        checksum=m.checksum,
    )


class SQLAlchemyCashAccountRepository(CashAccountRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, acc: CashAccount) -> CashAccount:
        self._session.add(
            CashAccountModel(
                id=str(acc.id),
                company_id=str(acc.company_id),
                code=acc.code,
                name=acc.name,
                opening_balance=acc.opening_balance,
                current_balance=acc.current_balance,
                is_system=acc.is_system,
                status=acc.status.value,
                created_at=acc.created_at,
                checksum=acc.checksum,
            )
        )
        self._session.commit()
        return acc

    def get_by_id(self, aid: UUID) -> CashAccount | None:
        m = self._session.get(CashAccountModel, str(aid))
        return _cash_to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[CashAccount]:
        rows = (
            self._session.query(CashAccountModel)
            .filter(CashAccountModel.company_id == str(cid))
            .all()
        )
        return [_cash_to_domain(r) for r in rows]

    def update(self, acc: CashAccount) -> CashAccount:
        m = self._session.get(CashAccountModel, str(acc.id))
        if m is None:
            raise ValueError("not found")
        m.current_balance = acc.current_balance
        m.status = acc.status.value
        m.checksum = acc.checksum
        self._session.commit()
        return acc

    def validate_code_unique(self, cid: UUID, code: str) -> bool:
        return not (
            self._session.query(CashAccountModel.id)
            .filter(
                CashAccountModel.company_id == str(cid),
                CashAccountModel.code == code,
            )
            .first()
        )


class ReconciliationModel(Base):
    __tablename__ = "bank_reconciliations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    bank_account_id: Mapped[str] = mapped_column(String(36), index=True)
    reconciliation_date: Mapped[date] = mapped_column(Date)
    statement_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    internal_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36))
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), default="")


def _rec_to_domain(m: ReconciliationModel) -> Reconciliation:
    return Reconciliation(
        id=UUID(m.id),
        company_id=UUID(m.company_id),
        bank_account_id=UUID(m.bank_account_id),
        reconciliation_date=m.reconciliation_date,
        statement_balance=Decimal(str(m.statement_balance)),
        internal_balance=Decimal(str(m.internal_balance)),
        created_by=UUID(m.created_by),
        is_resolved=m.is_resolved,
        resolved_at=m.resolved_at,
        approved_by=UUID(m.approved_by) if m.approved_by else None,
        checksum=m.checksum,
    )


class SQLAlchemyReconciliationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, r: Reconciliation) -> Reconciliation:
        self._session.add(
            ReconciliationModel(
                id=str(r.id),
                company_id=str(r.company_id),
                bank_account_id=str(r.bank_account_id),
                reconciliation_date=r.reconciliation_date,
                statement_balance=r.statement_balance,
                internal_balance=r.internal_balance,
                is_resolved=r.is_resolved,
                resolved_at=r.resolved_at,
                created_by=str(r.created_by),
                approved_by=str(r.approved_by) if r.approved_by else None,
                checksum=r.checksum,
            )
        )
        self._session.commit()
        return r

    def get_by_id(self, rid: UUID) -> Reconciliation | None:
        m = self._session.get(ReconciliationModel, str(rid))
        return _rec_to_domain(m) if m else None

    def update(self, r: Reconciliation) -> Reconciliation:
        m = self._session.get(ReconciliationModel, str(r.id))
        if m is None:
            raise ValueError("not found")
        m.is_resolved = r.is_resolved
        m.resolved_at = r.resolved_at
        m.approved_by = str(r.approved_by) if r.approved_by else None
        m.checksum = r.checksum
        self._session.commit()
        return r

    def get_by_company(self, cid: UUID) -> list[Reconciliation]:
        rows = (
            self._session.query(ReconciliationModel)
            .filter(ReconciliationModel.company_id == str(cid))
            .order_by(ReconciliationModel.reconciliation_date.desc())
            .all()
        )
        return [_rec_to_domain(r) for r in rows]
