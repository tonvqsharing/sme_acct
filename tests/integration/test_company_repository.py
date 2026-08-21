"""Tests for Company storage layer (SQLAlchemy repository)."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.company.domain import (
    AccountingRegime,
    Company,
    CompanyStatus,
    CompanyType,
    TaxId,
)
from src.bricks.company.storage import CompanyModel, SQLAlchemyCompanyRepository


@pytest.fixture
def engine():
    """Create in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    CompanyModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine)


@pytest.fixture
def repo(session_factory):
    """Create repository with fresh session."""
    session = session_factory()
    try:
        yield SQLAlchemyCompanyRepository(session)
    finally:
        session.close()


class TestCompanyModel:
    """CompanyModel mapping tests."""

    def test_create_company_model(self, session_factory):
        session = session_factory()
        model = CompanyModel(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst="0123456789",
            headquarters_address="123 Đường Lê Lợi",
            legal_representative="Nguyễn Văn A",
            company_type="multi_llc",
            accounting_regime="tt99",
            status="active",
            is_active=True,
        )
        session.add(model)
        session.commit()

        loaded = session.get(CompanyModel, model.id)
        assert loaded.legal_name == "Công ty TNHH ABC"
        assert loaded.mst == "0123456789"
        assert loaded.company_type == "multi_llc"
        session.close()

    def test_mst_unique_constraint(self, session_factory):
        session = session_factory()
        model1 = CompanyModel(
            id=uuid4(),
            legal_name="Company 1",
            mst="0123456789",
            company_type="multi_llc",
            accounting_regime="tt99",
            status="active",
            is_active=True,
        )
        model2 = CompanyModel(
            id=uuid4(),
            legal_name="Company 2",
            mst="0123456789",  # Duplicate MST
            company_type="multi_llc",
            accounting_regime="tt99",
            status="active",
            is_active=True,
        )
        session.add(model1)
        session.commit()

        from sqlalchemy.exc import IntegrityError

        session.add(model2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()

    def test_json_fields(self, session_factory):
        session = session_factory()
        model = CompanyModel(
            id=uuid4(),
            legal_name="Company JSON",
            mst="0123456789",
            company_type="multi_llc",
            accounting_regime="tt99",
            status="active",
            is_active=True,
            business_fields=["6201", "6202"],
            bank_accounts=[
                {"bank_name": "VietinBank", "account_number": "123", "is_primary": True}
            ],
        )
        session.add(model)
        session.commit()

        loaded = session.get(CompanyModel, model.id)
        assert loaded.business_fields == ["6201", "6202"]
        assert len(loaded.bank_accounts) == 1
        assert loaded.bank_accounts[0]["bank_name"] == "VietinBank"
        session.close()


class TestSQLAlchemyCompanyRepository:
    """Repository implementation tests."""

    def test_create(self, repo):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
            company_type=CompanyType.MULTI_LLC,
            accounting_regime=AccountingRegime.TT99,
        )
        created = repo.create(company)
        assert created.id == company.id
        assert created.legal_name == "Công ty TNHH ABC"

    def test_get_by_id(self, repo):
        company = Company(
            id=uuid4(),
            legal_name="Test Company",
            mst=TaxId("0123456789"),
        )
        repo.create(company)
        found = repo.get_by_id(company.id)
        assert found is not None
        assert found.legal_name == "Test Company"

    def test_get_by_id_not_found(self, repo):
        found = repo.get_by_id(uuid4())
        assert found is None

    def test_get_by_mst(self, repo):
        company = Company(
            id=uuid4(),
            legal_name="MST Company",
            mst=TaxId("0123456789"),
        )
        repo.create(company)
        found = repo.get_by_mst("0123456789")
        assert found is not None
        assert found.mst.value == "0123456789"

    def test_get_by_mst_not_found(self, repo):
        found = repo.get_by_mst("9999999999")
        assert found is None

    def test_list_active(self, repo):
        repo.create(
            Company(
                id=uuid4(),
                legal_name="Active 1",
                mst=TaxId("0123456789"),
                status=CompanyStatus.ACTIVE,
            )
        )
        repo.create(
            Company(
                id=uuid4(),
                legal_name="Suspended",
                mst=TaxId("0123456780"),
                status=CompanyStatus.SUSPENDED,
                is_active=False,
            )
        )
        repo.create(
            Company(
                id=uuid4(),
                legal_name="Active 2",
                mst=TaxId("0123456781"),
                status=CompanyStatus.ACTIVE,
            )
        )
        active = repo.list_active()
        assert len(active) == 2
        names = {c.legal_name for c in active}
        assert "Active 1" in names
        assert "Active 2" in names

    def test_update(self, repo):
        company = Company(
            id=uuid4(),
            legal_name="Original",
            mst=TaxId("0123456789"),
        )
        repo.create(company)
        actor = uuid4()
        company.legal_name = "Updated"
        updated = repo.update(company, actor)
        assert updated.legal_name == "Updated"

    def test_deactivate(self, repo):
        company = Company(
            id=uuid4(),
            legal_name="To Deactivate",
            mst=TaxId("0123456789"),
            status=CompanyStatus.ACTIVE,
            is_active=True,
        )
        repo.create(company)
        actor = uuid4()
        deactivated = repo.deactivate(company.id, actor)
        assert deactivated.status == CompanyStatus.SUSPENDED
        assert deactivated.is_active is False
