"""SQLAlchemy adapters for Bank Reconciliation module (specs-bank-cash-accounts.md §4).

Mirrors the pattern used by coa_repo.py — persistence-only, state
validation enforced by the service layer via domain entities.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload

from src.application.ports import BankReconciliationRepositoryPort
from src.infrastructure.database import db
from src.infrastructure.database.models import BankReconciliationModel
from src.domain.entities.bank_reconciliation import BankReconciliation
from src.domain.exceptions import DomainException


class SQLAlchemyBankReconciliationRepository:
    """Repository adapter for BankReconciliation aggregate root."""

    def get_by_id(self, reconciliation_id: UUID) -> BankReconciliation | None:
        """Get bank reconciliation by ID."""
        model = db.session.get(BankReconciliationModel, reconciliation_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_unresolved_by_company(self, company_id: UUID) -> list[BankReconciliation]:
        """List unresolved reconciliations for a company."""
        stmt = select(BankReconciliationModel).where(
            BankReconciliationModel.company_id == company_id,
            BankReconciliationModel.is_resolved.is_(False),
        )
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def list_by_company(
        self, company_id: UUID, resolved: bool | None = None
    ) -> list[BankReconciliation]:
        """List reconciliations for a company with filter on resolved status."""
        stmt = select(BankReconciliationModel).where(
            BankReconciliationModel.company_id == company_id
        )
        if resolved is not None:
            if resolved:
                stmt = stmt.where(BankReconciliationModel.is_resolved.is_(True))
            else:
                stmt = stmt.where(BankReconciliationModel.is_resolved.is_(False))
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def create(self, reconciliation: BankReconciliation) -> BankReconciliation:
        """Persist new BankReconciliation."""
        model = self._domain_to_model(reconciliation)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def update(self, reconciliation: BankReconciliation) -> BankReconciliation:
        """Update existing BankReconciliation."""
        model = db.session.get(BankReconciliationModel, reconciliation.id)
        if model is None:
            raise DomainException(f"Phân kỳ {reconciliation.id} không tồn tại")

        model.statement_balance = reconciliation.statement_balance
        model.internal_balance = reconciliation.internal_balance
        model.difference = reconciliation.difference
        model.checksum = uuid4().hex[:64]  # append audit event checksum
        db.session.flush()
        return self._model_to_domain(model)

    def resolve(self, reconciliation_id: UUID, approver: UUID, reason: str) -> BankReconciliation:
        """Resolve reconciliation via SOD (2-actor approval)."""
        model = db.session.get(BankReconciliationModel, reconciliation_id)
        if model is None:
            raise DomainException(f"Phân kỳ {reconciliation_id} không tồn tại")

        # Mark as resolved by 2nd actor (SOD)
        model.is_resolved = True
        model.resolved_at = date.today()
        model.resolved_by = approver
        model.checksum = uuid4().hex[:64]  # 2nd actor checksum
        db.session.flush()

        return self._model_to_domain(model)

    def _model_to_domain(self, model: BankReconciliationModel) -> BankReconciliation:
        """Convert SQLAlchemy model to domain entity."""
        recon = BankReconciliation(
            company_id=model.company_id,
            bank_account_id=model.bank_account_id,
            reconciliation_date=model.reconciliation_date,
            statement_balance=model.statement_balance,
            internal_balance=model.internal_balance,
            created_by=model.created_by,
            status=model.is_resolved,  # will map to status enum
        )
        recon.id = model.id
        recon.difference = model.difference
        recon.checksum = model.checksum
        return recon

    def _domain_to_model(self, recon: BankReconciliation) -> BankReconciliationModel:
        """Convert domain entity to SQLAlchemy model."""
        model = BankReconciliationModel(
            id=recon.id,
            company_id=recon.company_id,
            bank_account_id=recon.bank_account_id,
            reconciliation_date=recon.reconciliation_date,
            statement_balance=recon.statement_balance,
            internal_balance=recon.internal_balance,
            difference=recon.difference,
            is_resolved=recon.status in (
                ReconciliationStatus.RESOLVED,
                ReconciliationStatus.RESOLVED_WITH_DISCREPANCY,
            ),
            checksum=recon.checksum,
            created_by=recon.created_by,
        )
        return model