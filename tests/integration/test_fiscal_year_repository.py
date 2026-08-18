"""Integration tests — fiscal year + period lock repositories.

Plain SQLAlchemy, no Flask (conftest pattern). Covers test-plan I-01..I-05
+ legacy PeriodLockModel dual-write bridge (keeps currencies D8 path green).
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import close_all_sessions, sessionmaker

from src.domain.entities.base import AccountingPeriodType, PeriodLockAction, PeriodStatus
from src.domain.entities.fiscal_year import FiscalYear
from src.infrastructure.database import db
from src.infrastructure.database.models import Base, PeriodLockModel
from src.infrastructure.repositories.fiscal_year_repo import (
    SQLAlchemyFiscalYearRepository,
    SQLAlchemyPeriodLockRepository,
)

COMPANY = uuid4()
ACTOR = uuid4()


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
def fy_repo(session):
    return SQLAlchemyFiscalYearRepository()


@pytest.fixture()
def lock_repo(session):
    return SQLAlchemyPeriodLockRepository()


def _fy() -> FiscalYear:
    return FiscalYear(
        company_id=COMPANY,
        period_type=AccountingPeriodType.CALENDAR,
        start_date=date(2026, 1, 1),
    )


class TestFiscalYearRepo:
    def test_i01_save_and_get_active_roundtrip(self, fy_repo):
        fy = _fy()
        saved = fy_repo.save(fy)
        assert saved.id is not None

        got = fy_repo.get_active(COMPANY, date(2026, 6, 15))
        assert got is not None
        assert got.id == saved.id
        assert len(got.periods) == 12
        assert got.period_for_date(date(2026, 6, 15)).label == "Tháng 06/2026"

    def test_get_active_outside_range_returns_none(self, fy_repo):
        fy_repo.save(_fy())
        assert fy_repo.get_active(COMPANY, date(2025, 12, 31)) is None
        assert fy_repo.get_active(COMPANY, date(2027, 1, 1)) is None

    def test_list_by_company(self, fy_repo):
        fy_repo.save(_fy())
        years = fy_repo.list_by_company(COMPANY)
        assert len(years) == 1
        assert years[0].year_code == "2026"

    def test_i04_duplicate_year_code_rejected(self, fy_repo, session):
        fy_repo.save(_fy())
        dup = _fy()
        dup.id = uuid4()
        with pytest.raises(IntegrityError):
            fy_repo.save(dup)

    def test_status_persisted(self, fy_repo):
        fy = _fy()
        fy.periods[1].close(actor=ACTOR, reason="khóa")
        fy_repo.save(fy)
        got = fy_repo.get_active(COMPANY, date(2026, 2, 10))
        assert got.periods[1].status == PeriodStatus.LOCKED


class TestPeriodLockRepo:
    def test_i02_is_locked_overlap(self, lock_repo, fy_repo):
        fy = _fy()
        fy_repo.save(fy)
        period = fy.period_for_date(date(2026, 2, 10))

        assert lock_repo.is_locked(COMPANY, date(2026, 2, 10)) is False

        lock_repo.lock(period.id, actor=ACTOR, reason="khóa tháng 02")
        assert lock_repo.is_locked(COMPANY, date(2026, 2, 1)) is True
        assert lock_repo.is_locked(COMPANY, date(2026, 2, 28)) is True
        assert lock_repo.is_locked(COMPANY, date(2026, 3, 1)) is False
        assert lock_repo.is_locked(COMPANY, date(2026, 1, 31)) is False

    def test_i03_dual_write_legacy_periodlock(self, lock_repo, fy_repo, session):
        fy = _fy()
        fy_repo.save(fy)
        period = fy.period_for_date(date(2026, 3, 15))

        lock_repo.lock(period.id, actor=ACTOR, reason="khóa")
        rows = session.scalars(
            select(PeriodLockModel).where(PeriodLockModel.company_id == COMPANY)
        ).all()
        assert len(rows) == 1
        assert rows[0].is_locked is True
        assert rows[0].period_start == date(2026, 3, 1)

        lock_repo.reopen(period.id, actor=ACTOR, reason="mở lại")
        session.expire_all()
        rows = session.scalars(
            select(PeriodLockModel).where(PeriodLockModel.company_id == COMPANY)
        ).all()
        assert len(rows) == 0  # legacy lock cleared

    def test_i05_lock_event_chain(self, lock_repo, fy_repo):
        fy = _fy()
        fy_repo.save(fy)
        period = fy.period_for_date(date(2026, 2, 10))

        close_event = lock_repo.lock(period.id, actor=ACTOR, reason="khóa")
        reopen_event = lock_repo.reopen(period.id, actor=ACTOR, reason="điều chỉnh")

        events = lock_repo.history(period.id)
        assert [e.action for e in events] == [
            PeriodLockAction.CLOSE,
            PeriodLockAction.REOPEN,
        ]
        assert close_event.checksum
        assert reopen_event.prev_checksum == close_event.checksum
        assert reopen_event.checksum != close_event.checksum

    def test_find_period(self, lock_repo, fy_repo):
        fy = _fy()
        fy_repo.save(fy)
        period = lock_repo.find_period(COMPANY, date(2026, 11, 5))
        assert period is not None
        assert period.period_number == 11
        assert lock_repo.find_period(COMPANY, date(2026, 12, 31)).period_number == 12
