"""Regression: FX fields survive SQLite round-trip (C-1 fix proof)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.voucher.domain import JournalLine, Voucher, VoucherStatus
from src.bricks.voucher.storage import Base, SQLAlchemyVoucherRepository

C = uuid4()


@pytest.fixture()
def repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield SQLAlchemyVoucherRepository(sessionmaker(bind=engine)())
    engine.dispose()


def _voucher():
    return Voucher(
        company_id=C,
        number="PT/000001",
        entry_date=date(2026, 8, 1),
        description="fx round-trip regression",
        lines=[
            JournalLine(
                account_code="1121",
                debit=Decimal(25400000),
                credit=Decimal(0),
                currency_code="USD",
                fx_rate=Decimal(25400),
                amount_original=Decimal(1000),
            ),
            JournalLine(
                account_code="5111",
                debit=Decimal(0),
                credit=Decimal(25400000),
            ),
        ],
        status=VoucherStatus.DRAFT,
    )


class TestFxRoundTrip:
    def test_currency_fields_survive_sqlite(self, repo):
        created = repo.save(_voucher())
        loaded = repo.get_by_id(created.id)

        assert loaded is not None
        ln = loaded.lines[0]
        assert ln.currency_code == "USD"
        assert ln.fx_rate == Decimal(25400)
        assert ln.amount_original == Decimal(1000)

    def test_base_currency_lines_have_none_fx(self, repo):
        created = repo.save(_voucher())
        loaded = repo.get_by_id(created.id)
        assert loaded.lines[1].currency_code is None

    def test_bank_account_id_survives(self, repo):
        bid = uuid4()
        v = _voucher()
        v.lines[0].bank_account_id = bid
        repo.save(v)
        loaded = repo.get_by_id(v.id)
        assert loaded.lines[0].bank_account_id == bid
