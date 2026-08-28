"""COA account_type integration — persistence and auto-classification."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.coa.domain import Account, AccountType
from src.bricks.coa.storage import Base, SQLAlchemyAccountRepository

COMPANY = uuid4()


@pytest.fixture()
def repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield SQLAlchemyAccountRepository(sessionmaker(bind=engine)())
    engine.dispose()


class TestAccountTypePersistence:
    """account_type persists through storage round-trip."""

    def test_asset_type_persists(self, repo):
        repo.create(Account(company_id=COMPANY, code="111", name="Cash"))
        loaded = repo.get_by_code(COMPANY, "111")
        assert loaded is not None
        assert loaded.account_type == AccountType.ASSET

    def test_liability_type_persists(self, repo):
        repo.create(Account(company_id=COMPANY, code="211", name="Payable"))
        loaded = repo.get_by_code(COMPANY, "211")
        assert loaded is not None
        assert loaded.account_type == AccountType.LIABILITY

    def test_equity_type_persists(self, repo):
        repo.create(Account(company_id=COMPANY, code="311", name="Capital"))
        loaded = repo.get_by_code(COMPANY, "311")
        assert loaded is not None
        assert loaded.account_type == AccountType.EQUITY

    def test_revenue_type_persists(self, repo):
        repo.create(Account(company_id=COMPANY, code="411", name="Capital"))
        loaded = repo.get_by_code(COMPANY, "411")
        assert loaded is not None
        assert loaded.account_type == AccountType.REVENUE

    def test_expense_type_persists(self, repo):
        repo.create(Account(company_id=COMPANY, code="511", name="Revenue"))
        loaded = repo.get_by_code(COMPANY, "511")
        assert loaded is not None
        assert loaded.account_type == AccountType.EXPENSE

    def test_tt133_6xx_maps_to_expense(self, repo):
        repo.create(Account(company_id=COMPANY, code="632", name="COGS"))
        loaded = repo.get_by_code(COMPANY, "632")
        assert loaded is not None
        assert loaded.account_type == AccountType.EXPENSE

    def test_list_accounts_includes_type(self, repo):
        repo.create(Account(company_id=COMPANY, code="111", name="Cash"))
        repo.create(Account(company_id=COMPANY, code="211", name="Payable"))
        accounts = repo.get_by_company(COMPANY)
        types = {a.account_type for a in accounts}
        assert types == {AccountType.ASSET, AccountType.LIABILITY}
