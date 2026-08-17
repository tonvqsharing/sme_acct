"""Integration tests for CompanyRepository — plain SQLAlchemy, no Flask app context."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

from src.domain.entities.base import TaxId
from src.domain.entities.company import (
    AccountingRegime,
    BankAccount,
    Company,
    CompanyStatus,
    CompanyType,
)
from src.domain.exceptions import DuplicateMSTError
from src.infrastructure.repositories import SQLAlchemyCompanyRepository

FIXED_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXED_CREATOR = UUID("22222222-2222-2222-2222-222222222222")

_mst_counter = 0


def _make_kwargs(**overrides):
    global _mst_counter
    _mst_counter += 1
    # 10-digit MST, starts at 1000000001, 1000000002, ...
    mst_digits = f"{1_000_000_000 + _mst_counter}"
    base = {
        "id": uuid4(),
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": TaxId(mst_digits),
        "headquarters_address": "123 Nguyễn Văn Linh, Q.7, TP.HCM",
        "legal_representative": "Nguyễn Văn A",
        "business_reg_number": "0312345678",
        "business_reg_date": date(2020, 1, 15),
        "business_fields": ["6202", "4791"],
        "company_type": CompanyType.MULTI_LLC,
        "accounting_regime": AccountingRegime.TT99,
        "fiscal_year_start_month": 1,
        "fiscal_year_start_day": 1,
        "responsible_accountant_name": "Trần Thị B",
        "responsible_accountant_license": "KHMN-01234",
        "tax_agency": "Chi cục Thuế Q.7",
        "controlling_tax_office": "Cục Thuế TP.HCM",
        "bhxh_code": "0070123456",
        "bhxh_agency": "BHXH Quận 7",
        "authorized_capital": 1_000_000_000,
        "phone": "0281234567",
        "email": "info@abc.com",
        "website": "https://abc.com",
        "short_name": "ABC Co.",
        "bank_accounts": [
            BankAccount("VCB", "0071234567890", "Cty ABC", "PGD Q.7", is_primary=True),
        ],
        "status": CompanyStatus.ACTIVE,
        "is_active": True,
        "created_by": FIXED_CREATOR,
        "updated_by": FIXED_CREATOR,
        "config_version": 1,
        "legal_reviewed_at": None,
        "legal_reviewed_by": None,
        "mst_changed_at": None,
        "created_at": date(2024, 1, 1),
        "updated_at": date(2024, 1, 1),
    }
    base.update(overrides)
    return base


@pytest.fixture()
def repo():
    """SQLAlchemyCompanyRepository backed by an in-memory SQLite session.

    Replaces Flask-SQLAlchemy's scoped ``db.session`` with a plain
    SQLAlchemy session so tests don't need a live Flask app context.
    """
    from src.infrastructure.database import db
    from src.infrastructure.database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    plain_session = sessionmaker(bind=engine)()

    original = db.session
    db.session = plain_session
    try:
        yield SQLAlchemyCompanyRepository()
    finally:
        db.session = original
        close_all_sessions()
        engine.dispose()


class TestCompanyCreate:
    def test_create_persists(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        assert saved.id is not None
        assert saved.legal_name == "Công ty TNHH ABC Việt Nam"

    def test_create_bank_accounts_round_trip(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        fetched = repo.get_by_id(saved.id)
        assert len(fetched.bank_accounts) == 1
        ba = fetched.bank_accounts[0]
        assert ba.bank_name == "VCB"
        assert ba.is_primary is True

    def test_duplicate_mst_raises(self, repo):
        kwargs1 = _make_kwargs()
        kwargs2 = _make_kwargs()
        kwargs2["mst"] = kwargs1["mst"]  # share MST but different other fields
        c1 = Company(**kwargs1)
        repo.create(c1)
        c2 = Company(**kwargs2)
        with pytest.raises(DuplicateMSTError, match="đã được sử dụng"):
            repo.create(c2)

    def test_create_auto_fields(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        assert saved.config_version == 1
        assert saved.status == CompanyStatus.ACTIVE


class TestCompanyGet:
    def test_get_by_id_found(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        fetched = repo.get_by_id(saved.id)
        assert fetched.legal_name == c.legal_name

    def test_get_by_id_missing(self, repo):
        assert repo.get_by_id(UUID("99999999-9999-9999-9999-999999999999")) is None

    def test_get_by_mst(self, repo):
        c = Company(**_make_kwargs())
        company_mst = str(c.mst)
        repo.create(c)
        fetched = repo.get_by_mst(company_mst)
        assert fetched is not None
        assert str(fetched.mst) == company_mst

    def test_get_by_mst_branch_suffix(self, repo):
        c = Company(**_make_kwargs(mst=TaxId("0123456789-001")))
        repo.create(c)
        fetched = repo.get_by_mst("0123456789-001")
        assert str(fetched.mst) == "0123456789-001"

    def test_get_active(self, repo):
        c = Company(**_make_kwargs())
        repo.create(c)
        assert repo.get_active() is not None

    def test_get_active_dissolved_returns_none(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        saved.dissolve()
        repo.update(saved)
        assert repo.get_active() is None


class TestCompanyList:
    def test_list_two(self, repo):
        repo.create(Company(**_make_kwargs()))
        repo.create(Company(**_make_kwargs(legal_name="Cty B")))
        assert len(repo.list_active()) == 2

    def test_pagination(self, repo):
        for i in range(5):
            repo.create(Company(**_make_kwargs(legal_name=f"CT{i}")))
        page1 = repo.list_active(page=1, page_size=2)
        assert len(page1) == 2
        page2 = repo.list_active(page=2, page_size=2)
        assert len(page2) == 2

    def test_dissolved_excluded(self, repo):
        active = Company(**_make_kwargs())
        repo.create(active)
        dissolved = Company(**_make_kwargs(legal_name="Dissolved"))
        saved = repo.create(dissolved)
        saved.dissolve()
        repo.update(saved)
        results = repo.list_active()
        assert len(results) == 1


class TestCompanyLifecycle:
    def test_suspend_reactivate(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        saved.suspend()
        repo.update(saved)
        assert repo.get_by_id(saved.id).status == CompanyStatus.SUSPENDED
        fetched = repo.get_by_id(saved.id)
        fetched.reactivate()
        repo.update(fetched)
        assert repo.get_by_id(saved.id).status == CompanyStatus.ACTIVE

    def test_dissolve(self, repo):
        c = Company(**_make_kwargs())
        saved = repo.create(c)
        saved.dissolve()
        repo.update(saved)
        assert repo.get_by_id(saved.id).status == CompanyStatus.DISSOLVED
