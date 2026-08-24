"""COA storage — SQLAlchemy adapter."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.coa.contract import AccountRepositoryPort
from src.bricks.coa.domain import Account, AccountStatus, NormalBalance


class Base(DeclarativeBase):
    pass


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(4), index=True)
    name: Mapped[str] = mapped_column(String(200))
    parent_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    normal_balance: Mapped[str] = mapped_column(String(10), default="debit")
    status: Mapped[str] = mapped_column(String(20), default="active")

    __table_args__ = None


class SQLAlchemyAccountRepository(AccountRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: AccountModel) -> Account:
        return Account(
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            parent_code=m.parent_code,
            id=UUID(m.id),
            normal_balance=NormalBalance(m.normal_balance),
            status=AccountStatus(m.status),
        )

    def create(self, account: Account) -> Account:
        self._session.add(
            AccountModel(
                id=str(account.id),
                company_id=str(account.company_id),
                code=account.code,
                name=account.name,
                parent_code=account.parent_code,
                normal_balance=account.normal_balance.value,
                status=account.status.value,
            )
        )
        self._session.commit()
        return account

    def get_by_code(self, company_id: UUID, code: str) -> Account | None:
        m = (
            self._session.query(AccountModel)
            .filter(
                AccountModel.company_id == str(company_id),
                AccountModel.code == code,
            )
            .first()
        )
        return self._to_domain(m) if m else None

    def get_by_company(self, company_id: UUID) -> list[Account]:
        rows = (
            self._session.query(AccountModel)
            .filter(AccountModel.company_id == str(company_id))
            .order_by(AccountModel.code.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def update(self, account: Account) -> Account:
        m = self._session.get(AccountModel, str(account.id))
        if m is None:
            raise ValueError(f"Account {account.code} not found")
        m.name = account.name
        m.normal_balance = account.normal_balance.value
        m.status = account.status.value
        self._session.commit()
        return account

    def validate_code_unique(self, company_id: UUID, code: str) -> bool:
        exists = (
            self._session.query(AccountModel.id)
            .filter(
                AccountModel.company_id == str(company_id),
                AccountModel.code == code,
            )
            .first()
        )
        return exists is None
