"""Company service layer — CompanyService + TenantService.

Pure business logic. No Flask/SQLAlchemy imports.
Uses contract.py port for persistence.
"""

from __future__ import annotations

from uuid import UUID

from src.bricks.company.contract import CompanyRepositoryPort
from src.bricks.company.domain import (
    AccountingRegime,
    Company,
    CompanyType,
    DuplicateMSTError,
    TaxId,
)


class CompanyService:
    """Company CRUD + business logic."""

    def __init__(self, repo: CompanyRepositoryPort) -> None:
        self._repo = repo

    def create(
        self,
        legal_name: str,
        mst: str,
        company_type: CompanyType = CompanyType.MULTI_LLC,
        accounting_regime: AccountingRegime = AccountingRegime.TT99,
        created_by: UUID | None = None,
    ) -> Company:
        """Create new company. Raises DuplicateMSTError if MST exists."""
        existing = self._repo.get_by_mst(mst)
        if existing is not None:
            raise DuplicateMSTError(f"MST {mst} already registered")

        company = Company(
            legal_name=legal_name,
            mst=TaxId(mst),
            company_type=company_type,
            accounting_regime=accounting_regime,
            created_by=created_by,
        )
        return self._repo.create(company)

    def get_by_id(self, company_id: UUID) -> Company | None:
        return self._repo.get_by_id(company_id)

    def get_by_mst(self, mst: str) -> Company | None:
        return self._repo.get_by_mst(mst)

    def list_active(self) -> list[Company]:
        return self._repo.list_active()

    def update(self, company: Company, actor: UUID) -> Company:
        """Update company. Increments config_version."""
        company.config_version += 1
        return self._repo.update(company, actor=actor)

    def deactivate(self, company_id: UUID, actor: UUID) -> Company:
        """Soft-deactivate company (status → SUSPENDED, is_active → False)."""
        return self._repo.deactivate(company_id, actor=actor)


class TenantService:
    """Multi-tenant scoping — resolve company, check access."""

    def __init__(self, company_service: CompanyService) -> None:
        self._company_service = company_service

    def resolve_company(self, company_id: UUID) -> Company | None:
        return self._company_service.get_by_id(company_id)

    def check_access(self, company_id: UUID) -> bool:
        """Return True if company exists and is active."""
        company = self._company_service.get_by_id(company_id)
        if company is None:
            return False
        return company.is_active
