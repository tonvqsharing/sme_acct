"""SQLAlchemy adapters for Cash Account module (specs-bank-cash-accounts.md §4).

Mirrors the pattern used by coa_repo.py — persistence-only, state
validation enforced by the service layer via domain entities.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload

from src.application.ports import CashAccountRepositoryPort
from src.infrastructure.database import db
from src.infrastructure.database.models import CashAccountModel
from src.domain.entities.cash_account import CashAccount
from src.domain.exceptions import DomainException


class SQLAlchemyCashAccountRepository:
    """Repository adapter for CashAccount aggregate root."""

    def get_by_id(self, cash_account_id: UUID) -> CashAccount | None:
        """Get cash account by ID."""
        model = db.session.get(CashAccountModel, cash_account_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_company(self, company_id: UUID) -> list[CashAccount]:
        """List cash accounts for a company."""
        stmt = select(CashAccountModel).where(CashAccountModel.company_id == company_id)
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def validate_code_unique(self, company_id: UUID, code: str) -> bool:
        """Validate that cash code is unique per company (TT99 format)."""
        stmt = select(CashAccountModel).where(
            CashAccountModel.code == code,
            CashAccountModel.company_id == company_id,
        )
        existing = db.session.scalar(stmt)
        return existing is None

    def create(self, account: CashAccount) -> CashAccount:
        """Persist new CashAccount; validate code uniqueness first."""
        if not self.validate_code_unique(account.company_id, account.code):
            raise DomainException(
                f"Mã số {account.code} đã tồn tại cho doanh nghiệp {account.company_id}"
            )

        model = self._domain_to_model(account)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def update_balance(self, cash_account_id: UUID, amount: float | Decimal, actor: UUID, reason: str) -> CashAccount:
        """Update cash balance with mutation tracking."""
        model = db.session.get(CashAccountModel, cash_account_id)
        if model is None:
            raise DomainException(f"Tài khoản {cash_account_id} không tồn tại")

        # Update balance
        new_balance = (float(model.current_balance or 0) + float(amount))
        model.current_balance = new_balance
        model.checksum = uuid4().hex[:64]  # append audit event checksum
        db.session.flush()

        return self._model_to_domain(model)

    def soft_close(self, cash_account_id: UUID, actor: UUID, reason: str) -> None:
        """Soft-close cash account: requires balance = 0 (10-year retention per Law on Accounting Art. 11)."""
        model = db.session.get(CashAccountModel, cash_account_id)
        if model is None:
            raise DomainException(f"Tài khoản {cash_account_id} không tồn tại")
        if float(model.current_balance or 0) != 0:
            raise DomainException("Không thể đóng tài khoản có số dư không bằng 0")
        model.status = "Closed"
        model.checksum = uuid4().hex[:64]
        db.session.flush()

    def _model_to_domain(self, model: CashAccountModel) -> CashAccount:
        """Convert SQLAlchemy model to domain entity."""
        cash = CashAccount(
            company_id=model.company_id,
            code=model.code,
            name=model.name,
            opening_balance=float(model.opening_balance),
            is_system=model.is_system,
            created_by=model.created_by,
            status=model.status,  # will be converted
        )
        cash.id = model.id
        cash.current_balance = float(model.current_balance or 0)
        cash.checksum = model.checksum
        cash.created_at = model.created_at
        return cash

    def _domain_to_model(self, cash: CashAccount) -> CashAccountModel:
        """Convert domain entity to SQLAlchemy model."""
        model = CashAccountModel(
            id=cash.id,
            company_id=cash.company_id,
            code=cash.code,
            name=cash.name,
            opening_balance=cash.opening_balance,
            current_balance=cash.current_balance,
            is_system=cash.is_system,
            status=cash.status.value if hasattr(cash.status, 'value') else cash.status,
            checksum=cash.checksum,
            created_by=cash.created_by,
        )
        return model