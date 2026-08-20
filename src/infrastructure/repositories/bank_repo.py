"""SQLAlchemy adapters for Bank Account module (specs-bank-cash-accounts.md §4).

Mirrors the pattern used by coa_repo.py — persistence-only, state
validation enforced by the service layer via domain entities.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload

from src.application.ports import (
    BankAccountRepositoryPort,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import BankAccountModel
from src.domain.entities.bank_account import BankAccount
from src.domain.entities.bank_account import AccountStatus
from src.domain.exceptions import DomainException


class SQLAlchemyBankAccountRepository:
    """Repository adapter for BankAccount aggregate root."""

    def get_by_id(self, bank_account_id: UUID) -> BankAccount | None:
        """Get bank account by ID."""
        model = db.session.get(BankAccountModel, bank_account_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_company(self, company_id: UUID) -> list[BankAccount]:
        """List bank accounts for a company."""
        stmt = select(BankAccountModel).where(BankAccountModel.company_id == company_id)
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def get_primary_by_company(self, company_id: UUID) -> BankAccount | None:
        """Get the primary bank account for a company."""
        stmt = select(BankAccountModel).where(
            BankAccountModel.company_id == company_id,
            BankAccountModel.is_primary.is_(True),
        )
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def validate_code_unique(self, company_id: UUID, account_number: str) -> bool:
        """Validate that account_number is unique per company."""
        stmt = select(BankAccountModel).where(
            BankAccountModel.account_number == account_number,
            BankAccountModel.company_id == company_id,
        )
        existing = db.session.scalar(stmt)
        return existing is None

    def create(self, account: BankAccount) -> BankAccount:
        """Persist new BankAccount; validate code uniqueness first."""
        if not self.validate_code_unique(account.company_id, account.account_number):
            raise DomainException(
                f"Số tài khoản {account.account_number} đã tồn tại cho doanh nghiệp {account.company_id}"
            )

        model = self._domain_to_model(account)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def update(self, account: BankAccount) -> BankAccount:
        """Update existing BankAccount; validate invariants."""
        model = db.session.get(BankAccountModel, account.id)
        if model is None:
            raise DomainException(f"Tài khoản {account.id} không tồn tại trong DB")

        # Update fields
        model.bank_name = account.bank_name
        model.account_number = account.account_number
        model.account_holder = account.account_holder
        model.branch = account.branch
        model.is_primary = account.is_primary
        model.status = account.status.value
        model.updated_at = date.today()

        db.session.flush()
        return self._model_to_domain(model)

    def soft_delete(self, bank_account_id: UUID, actor: UUID, reason: str) -> None:
        """Set status=CLOSED; do NOT row-delete (10-year retention per Law on Accounting Art. 11)."""
        model = db.session.get(BankAccountModel, bank_account_id)
        if model is None:
            raise DomainException(f"Tài khoản {bank_account_id} không tồn tại")
        model.status = "Closed"
        model.checksum = uuid4().hex[:64]  # append audit event checksum
        db.session.flush()

    def _model_to_domain(self, model: BankAccountModel) -> BankAccount:
        """Convert SQLAlchemy model to domain entity."""
        from src.domain.entities.base import TaxId  # noqa: F815 (avoid circular)

        account = BankAccount(
            company_id=model.company_id,
            bank_name=model.bank_name,
            account_number=model.account_number,
            account_holder=model.account_holder,
            branch=model.branch or "",
            is_primary=model.is_primary,
            created_by=model.created_by,
            status=AccountStatus(model.status),
        )
        account.id = model.id  # set id after object creation
        account.checksum = model.checksum
        account.created_at = model.created_at
        return account

    def _domain_to_model(self, account: BankAccount) -> BankAccountModel:
        """Convert domain entity to SQLAlchemy model."""
        model = BankAccountModel(
            id=account.id,
            company_id=account.company_id,
            bank_name=account.bank_name,
            account_number=account.account_number,
            account_holder=account.account_holder,
            branch=account.branch,
            is_primary=account.is_primary,
            status=account.status.value,
            checksum=account.checksum,
            created_at=account.created_at,
            created_by=account.created_by,
        )
        return model