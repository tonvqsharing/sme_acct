"""Integration tests for currency repositories — plain SQLAlchemy, no Flask.

Mirrors tests/integration/conftest.py pattern: in-memory SQLite + db.session swap.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

from src.domain.entities.base import PostingSide, RateType, RevaluationStatus
from src.domain.entities.currency import (
    Currency,
    ExchangeRate,
    RevaluationEntry,
    RevaluationRun,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.currency_repo import (
    SQLAlchemyCurrencyRepository,
    SQLAlchemyExchangeRateRepository,
    SQLAlchemyRevaluationRepository,
)

FIXED_ACTOR = uuid4()
FIXED_COMPANY = uuid4()


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    plain = sessionmaker(bind=engine)()
    original = db.session
    db.session = plain  # type: ignore[assignment]
    try:
        yield plain
    finally:
        db.session = original
        close_all_sessions()
        engine.dispose()


@pytest.fixture()
def cur_repo(session):
    return SQLAlchemyCurrencyRepository()


@pytest.fixture()
def rate_repo(session):
    return SQLAlchemyExchangeRateRepository()


@pytest.fixture()
def reval_repo(session):
    return SQLAlchemyRevaluationRepository()


def _usd():
    return Currency(code="USD", name="US Dollar", symbol="$")


# ── CurrencyRepositoryPort ─────────────────────────────────────────────────


class TestCurrencyRepo:
    def test_save_and_get_roundtrip(self, cur_repo):
        cur_repo.save(_usd())
        got = cur_repo.get("USD")
        assert got is not None
        assert got.code == "USD"
        assert got.decimal_places == 2

    def test_save_existing_updates(self, cur_repo):
        cur_repo.save(_usd())
        cur_repo.save(Currency(code="USD", name="US Dollar Updated", symbol="US$"))
        assert cur_repo.get("USD").name == "US Dollar Updated"

    def test_exists(self, cur_repo):
        assert cur_repo.exists("USD") is False
        cur_repo.save(_usd())
        assert cur_repo.exists("USD") is True

    def test_list_active_filters_inactive(self, cur_repo):
        cur_repo.save(_usd())
        cur_repo.save(Currency(code="EUR", name="Euro", symbol="€"))
        cur_repo.save(Currency(code="JPY", name="Yen", symbol="¥"))
        # Deactivate EUR
        from src.infrastructure.database.models import CurrencyModel

        eur = db.session.get(CurrencyModel, "EUR")
        eur.is_active = False
        db.session.commit()
        codes = [c.code for c in cur_repo.list_active()]
        assert codes == ["JPY", "USD"]


# ── ExchangeRateRepositoryPort ─────────────────────────────────────────────


class TestExchangeRateRepo:
    def _rate(self, rate_date, rate, rate_type=RateType.BUY):
        return ExchangeRate(
            currency_code="USD",
            rate_date=rate_date,
            rate_type=rate_type,
            rate=Decimal(rate),
            source="MANUAL",
            actor=FIXED_ACTOR,
        )

    def test_create_and_latest_exact_date(self, rate_repo, cur_repo):
        cur_repo.save(_usd())
        rate_repo.create(self._rate(date(2026, 8, 1), "24700"))
        got = rate_repo.get_latest("USD", RateType.BUY, date(2026, 8, 1))
        assert got is not None
        assert got.rate == Decimal("24700")

    def test_get_latest_falls_back_to_previous_date(self, rate_repo, cur_repo):
        """Tryton semantics: last available rate ≤ date used for gaps."""
        cur_repo.save(_usd())
        rate_repo.create(self._rate(date(2026, 8, 1), "24700"))
        rate_repo.create(self._rate(date(2026, 8, 15), "24900"))
        got = rate_repo.get_latest("USD", RateType.BUY, date(2026, 8, 10))
        assert got.rate == Decimal("24700")

    def test_latest_prefers_newest_rate(self, rate_repo, cur_repo):
        cur_repo.save(_usd())
        rate_repo.create(self._rate(date(2026, 8, 1), "24700"))
        rate_repo.create(self._rate(date(2026, 8, 15), "24900"))
        got = rate_repo.get_latest("USD", RateType.BUY, date(2026, 8, 20))
        assert got.rate == Decimal("24900")

    def test_list_history_filters(self, rate_repo, cur_repo):
        cur_repo.save(_usd())
        cur_repo.save(Currency(code="EUR", name="Euro", symbol="€"))
        rate_repo.create(self._rate(date(2026, 8, 1), "24700"))
        rate_repo.create(self._rate(date(2026, 8, 15), "24900"))
        eur_rate = ExchangeRate(
            currency_code="EUR",
            rate_date=date(2026, 8, 1),
            rate_type=RateType.BUY,
            rate=Decimal("26800"),
            source="MANUAL",
            actor=FIXED_ACTOR,
        )
        rate_repo.create(eur_rate)
        usd_rates = rate_repo.list_history("USD", None, None, None)
        assert len(usd_rates) == 2
        aug_rates = rate_repo.list_history("USD", None, date(2026, 8, 1), date(2026, 8, 14))
        assert len(aug_rates) == 1

    def test_duplicate_same_date_type_rejected(self, rate_repo, cur_repo):
        """Unique (currency, date, type) per specs §5; supersede = later date."""
        from sqlalchemy.exc import IntegrityError

        cur_repo.save(_usd())
        rate_repo.create(self._rate(date(2026, 8, 1), "24700"))
        with pytest.raises(IntegrityError):
            rate_repo.create(self._rate(date(2026, 8, 1), "24800"))


# ── RevaluationRepositoryPort ──────────────────────────────────────────────


class TestRevaluationRepo:
    def _entry(self, difference=Decimal("700000")):
        return RevaluationEntry(
            account_code="1122",
            currency_code="USD",
            balance_original=Decimal("1000"),
            rate_applied=Decimal("24700"),
            old_vnd=Decimal("24000000"),
            new_vnd=Decimal("24700000"),
            difference=difference,
            posting_side=PostingSide.DEBIT,
        )

    def _offset(self, difference=Decimal("-700000")):
        return RevaluationEntry(
            account_code="5151",
            currency_code="USD",
            balance_original=Decimal("0"),
            rate_applied=Decimal("24700"),
            old_vnd=Decimal("0"),
            new_vnd=Decimal("0"),
            difference=difference,
            posting_side=PostingSide.CREDIT,
        )

    def _run(self):
        return RevaluationRun(
            company_id=FIXED_COMPANY,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            rate_date=date(2026, 8, 31),
            actor=FIXED_ACTOR,
            entries=[self._entry(), self._offset()],
        )

    def test_create_and_get_run(self, reval_repo, cur_repo):
        cur_repo.save(_usd())
        run = reval_repo.create_run(self._run())
        assert run.id is not None
        got = reval_repo.get_run(run.id)
        assert got is not None
        assert got.status == RevaluationStatus.DRAFT
        assert len(got.entries) == 2
        assert got.entries[0].account_code == "1122"

    def test_save_run_persists_status_change(self, reval_repo, cur_repo):
        cur_repo.save(_usd())
        run = reval_repo.create_run(self._run())
        run.submit_for_approval()
        run.approve(FIXED_ACTOR)
        reval_repo.save_run(run)
        got = reval_repo.get_run(run.id)
        assert got.status == RevaluationStatus.APPROVED
        assert got.approver == FIXED_ACTOR

    def test_get_posted_run_for_idempotency(self, reval_repo, cur_repo):
        cur_repo.save(_usd())
        run = self._run()
        reval_repo.create_run(run)
        run.submit_for_approval()
        run.approve(FIXED_ACTOR)
        run.post()
        reval_repo.save_run(run)
        posted = reval_repo.get_posted_run(FIXED_COMPANY, date(2026, 8, 1), date(2026, 8, 31))
        assert posted is not None
        assert posted.id == run.id
        # different period → none
        other = reval_repo.get_posted_run(FIXED_COMPANY, date(2026, 9, 1), date(2026, 9, 30))
        assert other is None

    def test_period_lock_detection(self, reval_repo, cur_repo):
        cur_repo.save(_usd())
        from src.infrastructure.database.models import PeriodLockModel

        db.session.add(
            PeriodLockModel(
                company_id=FIXED_COMPANY,
                period_start=date(2026, 8, 1),
                period_end=date(2026, 8, 31),
                is_locked=True,
                locked_by_id=FIXED_ACTOR,
            )
        )
        db.session.commit()
        assert (
            reval_repo.period_is_locked(FIXED_COMPANY, date(2026, 8, 1), date(2026, 8, 31)) is True
        )
        assert (
            reval_repo.period_is_locked(FIXED_COMPANY, date(2026, 9, 1), date(2026, 9, 30)) is False
        )
