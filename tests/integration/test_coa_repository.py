"""COA repo integration — SQLite persistence incl. tenant scoping."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.coa.domain import Account, AccountStatus, NormalBalance
from src.bricks.coa.storage import Base, SQLAlchemyAccountRepository

A, B = uuid4(), uuid4()


@pytest.fixture()
def repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield SQLAlchemyAccountRepository(sessionmaker(bind=engine)())
    engine.dispose()


class TestAccountRepo:
    def test_round_trip_preserves_fields(self, repo):
        acc = repo.create(
            Account(
                company_id=A,
                code="1121",
                name="TGNH VTB",
                normal_balance=NormalBalance.DEBIT,
            )
        )
        loaded = repo.get_by_code(A, "1121")
        assert loaded is not None
        assert loaded.name == "TGNH VTB"
        assert loaded.is_detail is True
        assert acc.id == loaded.id

    def test_tenant_scoped_lookup(self, repo):
        repo.create(Account(company_id=A, code="111", name="A-cash"))
        assert repo.get_by_code(B, "111") is None
        assert repo.validate_code_unique(B, "111") is True
        assert repo.validate_code_unique(A, "111") is False

    def test_update_status_persists(self, repo):
        repo.create(Account(company_id=A, code="111", name="Cash"))
        acc = repo.get_by_code(A, "111")
        assert acc is not None
        acc.status = AccountStatus.INACTIVE
        repo.update(acc)
        again = repo.get_by_code(A, "111")
        assert again is not None and again.status == AccountStatus.INACTIVE

    def test_list_ordered_by_code(self, repo):
        for c in ("331", "111", "511"):
            repo.create(Account(company_id=A, code=c, name=c))
        codes = [a.code for a in repo.get_by_company(A)]
        assert codes == ["111", "331", "511"]
