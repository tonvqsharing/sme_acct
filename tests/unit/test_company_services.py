"""Tests for Company service layer — CompanyService + TenantService.

TDD: RED phase — write tests before implementation.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.bricks.company.domain import (
    AccountingRegime,
    Company,
    CompanyStatus,
    CompanyType,
    DuplicateMSTError,
)

# ─── Fakes ────────────────────────────────────────────────────────────────


class FakeCompanyRepository:
    """In-memory fake for CompanyRepositoryPort."""

    def __init__(self):
        self._store: dict[UUID, Company] = {}
        self._by_mst: dict[str, UUID] = {}

    def create(self, company: Company) -> Company:
        if company.mst.value in self._by_mst:
            raise DuplicateMSTError(f"MST {company.mst.value} already exists")
        self._store[company.id] = company
        self._by_mst[company.mst.value] = company.id
        return company

    def get_by_id(self, company_id: UUID) -> Company | None:
        return self._store.get(company_id)

    def get_by_mst(self, mst: str) -> Company | None:
        cid = self._by_mst.get(mst)
        if cid:
            return self._store.get(cid)
        return None

    def list_active(self) -> list[Company]:
        return [c for c in self._store.values() if c.is_active]

    def update(self, company: Company, actor: UUID) -> Company:
        self._store[company.id] = company
        return company

    def deactivate(self, company_id: UUID, actor: UUID) -> Company:
        c = self._store.get(company_id)
        if c:
            c.status = CompanyStatus.SUSPENDED
            c.is_active = False
        return c

    def list_subsidiaries(self, parent_id: UUID) -> list[Company]:
        return []


# ─── CompanyService Tests ─────────────────────────────────────────────────


class TestCompanyService:
    """CompanyService CRUD + business logic tests."""

    def _make_service(self):
        from src.bricks.company.services import CompanyService

        return CompanyService(FakeCompanyRepository())

    def test_create_company(self):
        svc = self._make_service()
        actor = uuid4()
        company = svc.create(
            legal_name="Công ty TNHH ABC",
            mst="0123456789",
            company_type=CompanyType.MULTI_LLC,
            accounting_regime=AccountingRegime.TT99,
            created_by=actor,
        )
        assert company.legal_name == "Công ty TNHH ABC"
        assert company.mst.value == "0123456789"
        assert company.status == CompanyStatus.ACTIVE
        assert company.created_by == actor

    def test_create_company_duplicate_mst(self):
        svc = self._make_service()
        svc.create(legal_name="C1", mst="0123456789")
        with pytest.raises(DuplicateMSTError):
            svc.create(legal_name="C2", mst="0123456789")

    def test_get_company(self):
        svc = self._make_service()
        created = svc.create(legal_name="Test", mst="0123456789")
        found = svc.get_by_id(created.id)
        assert found is not None
        assert found.legal_name == "Test"

    def test_get_company_not_found(self):
        svc = self._make_service()
        assert svc.get_by_id(uuid4()) is None

    def test_get_by_mst(self):
        svc = self._make_service()
        svc.create(legal_name="Test", mst="0123456789")
        found = svc.get_by_mst("0123456789")
        assert found is not None
        assert found.mst.value == "0123456789"

    def test_get_by_mst_not_found(self):
        svc = self._make_service()
        assert svc.get_by_mst("9999999999") is None

    def test_list_active(self):
        svc = self._make_service()
        svc.create(legal_name="Active", mst="0123456789")
        active = svc.list_active()
        assert len(active) == 1

    def test_update_company(self):
        svc = self._make_service()
        actor = uuid4()
        company = svc.create(legal_name="Original", mst="0123456789")
        company.legal_name = "Updated"
        updated = svc.update(company, actor=actor)
        assert updated.legal_name == "Updated"
        assert updated.config_version == 1

    def test_deactivate_company(self):
        svc = self._make_service()
        actor = uuid4()
        company = svc.create(legal_name="Deactivate Me", mst="0123456789")
        deactivated = svc.deactivate(company.id, actor=actor)
        assert deactivated.status == CompanyStatus.SUSPENDED
        assert deactivated.is_active is False

    def test_update_increments_config_version(self):
        svc = self._make_service()
        actor = uuid4()
        company = svc.create(legal_name="Versioned", mst="0123456789")
        assert company.config_version == 0
        svc.update(company, actor=actor)
        assert company.config_version == 1


# ─── TenantService Tests ──────────────────────────────────────────────────


class TestTenantService:
    """TenantService multi-tenant scoping tests."""

    def _make_services(self):
        from src.bricks.company.services import CompanyService, TenantService

        repo = FakeCompanyRepository()
        company_svc = CompanyService(repo)
        tenant_svc = TenantService(company_svc)
        return company_svc, tenant_svc

    def test_resolve_company(self):
        company_svc, tenant_svc = self._make_services()
        company = company_svc.create(legal_name="Tenant", mst="0123456789")
        resolved = tenant_svc.resolve_company(company.id)
        assert resolved is not None
        assert resolved.legal_name == "Tenant"

    def test_resolve_company_not_found(self):
        _, tenant_svc = self._make_services()
        assert tenant_svc.resolve_company(uuid4()) is None

    def test_check_access_active_company(self):
        company_svc, tenant_svc = self._make_services()
        company = company_svc.create(legal_name="Tenant", mst="0123456789")
        assert tenant_svc.check_access(company.id) is True

    def test_check_access_deactivated_company(self):
        company_svc, tenant_svc = self._make_services()
        company = company_svc.create(legal_name="Tenant", mst="0123456789")
        company_svc.deactivate(company.id, actor=uuid4())
        assert tenant_svc.check_access(company.id) is False

    def test_check_access_nonexistent_company(self):
        _, tenant_svc = self._make_services()
        assert tenant_svc.check_access(uuid4()) is False
