"""Unit tests — PeriodLockService (fake repos, no DB).

Covers test-plan S-01..S-10: lazy FY auto-seed, quarter-aligned creation,
overlap rejection, lock/unlock, SOD self-approval block, year close.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from src.application.ports import FiscalYearRepositoryPort, PeriodLockRepositoryPort
from src.application.services.period_lock_service import PeriodLockService
from src.domain.entities.base import AccountingPeriodType, PeriodLockAction, PeriodStatus
from src.domain.entities.fiscal_year import AccountingPeriod, FiscalYear, PeriodLockEvent
from src.domain.exceptions import (
    FiscalYearExistsError,
    InvalidFiscalYearError,
    NotFoundError,
    PeriodLockedError,
    PeriodTransitionError,
    SelfApprovalError,
    YearEndPreconditionsError,
)

COMPANY = uuid4()
ACTOR = uuid4()


class FakeFyRepo(FiscalYearRepositoryPort):
    def __init__(self) -> None:
        self.years: dict[UUID, FiscalYear] = {}

    def save(self, fiscal_year: FiscalYear) -> FiscalYear:
        if fiscal_year.id is None:
            raise ValueError("id required")
        self.years[fiscal_year.id] = fiscal_year
        return fiscal_year

    def get_active(self, company_id: UUID, entry_date: date) -> FiscalYear | None:
        for fy in self.years.values():
            if (
                fy.company_id == company_id
                and fy.end_date is not None
                and fy.start_date <= entry_date <= fy.end_date
            ):
                return fy
        return None

    def get_by_id(self, fiscal_year_id: UUID) -> FiscalYear | None:
        return self.years.get(fiscal_year_id)

    def list_by_company(self, company_id: UUID) -> list[FiscalYear]:
        return sorted(
            (fy for fy in self.years.values() if fy.company_id == company_id),
            key=lambda fy: fy.start_date,
        )


class FakeLockRepo(PeriodLockRepositoryPort):
    def __init__(self, fy_repo: FakeFyRepo) -> None:
        self.fy_repo = fy_repo
        self.events: list[PeriodLockEvent] = []

    def get_period(self, period_id: UUID) -> AccountingPeriod | None:
        for fy in self.fy_repo.years.values():
            for p in fy.periods:
                if p.id == period_id:
                    return p
        return None

    def find_period(self, company_id: UUID, entry_date: date) -> AccountingPeriod | None:
        fy = self.fy_repo.get_active(company_id, entry_date)
        if fy is None:
            return None
        return fy.period_for_date(entry_date)

    def is_locked(self, company_id: UUID, entry_date: date) -> bool:
        p = self.find_period(company_id, entry_date)
        return p is not None and p.status != PeriodStatus.OPEN

    def lock(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        # Mirrors SQLAlchemyPeriodLockRepository: persistence only — state
        # guard is enforced by the service via AccountingPeriod.close().
        p = self.get_period(period_id)
        if p is None:
            raise NotFoundError("period", str(period_id))
        p.status = PeriodStatus.LOCKED
        p.locked_by = actor
        p.locked_at = datetime.now()
        p.lock_reason = reason
        ev = PeriodLockEvent(
            period_id=period_id,
            action=PeriodLockAction.CLOSE,
            requested_by=actor,
            reason=reason,
            requested_at=datetime.now(),
        )
        self.events.append(ev)
        return ev

    def reopen(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        # Mirrors SQLAlchemyPeriodLockRepository: persistence only.
        p = self.get_period(period_id)
        if p is None:
            raise NotFoundError("period", str(period_id))
        p.status = PeriodStatus.OPEN
        p.locked_by = None
        p.locked_at = None
        p.lock_reason = None
        ev = PeriodLockEvent(
            period_id=period_id,
            action=PeriodLockAction.REOPEN,
            requested_by=actor,
            reason=reason,
            requested_at=datetime.now(),
        )
        self.events.append(ev)
        return ev

    def history(self, period_id: UUID) -> list[PeriodLockEvent]:
        return [e for e in self.events if e.period_id == period_id]


@pytest.fixture()
def service() -> tuple[PeriodLockService, FakeFyRepo, FakeLockRepo]:
    fy_repo = FakeFyRepo()
    lock_repo = FakeLockRepo(fy_repo)
    return PeriodLockService(fy_repo, lock_repo), fy_repo, lock_repo


class TestEnsureFiscalYear:
    def test_s01_auto_seed_default_calendar(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        assert fy.year_code == "2026"
        assert fy.period_type == AccountingPeriodType.CALENDAR
        assert fy.start_date == date(2026, 1, 1)
        assert len(fy.periods) == 12

    def test_idempotent(self, service):
        svc, fy_repo, _ = service
        fy1 = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        fy2 = svc.ensure_fiscal_year(COMPANY, date(2026, 9, 1))
        assert fy1.id == fy2.id
        assert len(fy_repo.years) == 1

    def test_returns_existing_containing_date(self, service):
        svc, fy_repo, _ = service
        svc.create_fiscal_year(COMPANY, AccountingPeriodType.CALENDAR, date(2026, 1, 1), ACTOR)
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 6, 1))
        assert fy.id is not None
        assert len(fy_repo.years) == 1


class TestCreateFiscalYear:
    def test_s02_valid_quarter_aligned(self, service):
        svc, fy_repo, _ = service
        fy = svc.create_fiscal_year(
            COMPANY, AccountingPeriodType.FISCAL_APR, date(2026, 4, 1), ACTOR
        )
        assert fy.periods[0].label == "Tháng 04/2026"
        assert len(fy.periods) == 12
        assert fy.end_date == date(2027, 3, 31)

    def test_s03_non_quarter_start_rejected(self, service):
        svc, fy_repo, _ = service
        with pytest.raises(InvalidFiscalYearError):
            svc.create_fiscal_year(COMPANY, AccountingPeriodType.CALENDAR, date(2026, 2, 1), ACTOR)

    def test_s04_overlap_rejected(self, service):
        svc, fy_repo, _ = service
        svc.create_fiscal_year(COMPANY, AccountingPeriodType.CALENDAR, date(2026, 1, 1), ACTOR)
        with pytest.raises(FiscalYearExistsError):
            svc.create_fiscal_year(
                COMPANY, AccountingPeriodType.FISCAL_JUL, date(2026, 7, 1), ACTOR
            )


class TestPeriodLock:
    def test_s05_is_locked_and_validate(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        assert svc.is_locked(COMPANY, date(2026, 2, 10)) is False

        svc.close_period(p2.id, ACTOR, "khóa tháng 02")
        assert svc.is_locked(COMPANY, date(2026, 2, 10)) is True
        with pytest.raises(PeriodLockedError):
            svc.validate_before_entry(COMPANY, date(2026, 2, 10))

    def test_s06_close_period_event(self, service):
        svc, fy_repo, lock_repo = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        ev = svc.close_period(p2.id, ACTOR, "khóa")
        assert ev.action == PeriodLockAction.CLOSE
        assert len(lock_repo.history(p2.id)) == 1

    def test_s07_double_close_rejected(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        svc.close_period(p2.id, ACTOR, "khóa")
        with pytest.raises(PeriodTransitionError):
            svc.close_period(p2.id, ACTOR, "khóa lại")

    def test_s08_reopen_requires_reason(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        svc.close_period(p2.id, ACTOR, "khóa")
        with pytest.raises(PeriodTransitionError):
            svc.reopen_period(p2.id, ACTOR, "   ")

    def test_s09_reopen_self_approval_blocked(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        svc.close_period(p2.id, ACTOR, "khóa")
        with pytest.raises(SelfApprovalError):
            svc.reopen_period(p2.id, ACTOR, "mở lại")

    def test_reopen_by_other_user(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        svc.close_period(p2.id, ACTOR, "khóa")
        other = uuid4()
        ev = svc.reopen_period(p2.id, other, "điều chỉnh")
        assert ev.action == PeriodLockAction.REOPEN
        assert svc.is_locked(COMPANY, date(2026, 2, 10)) is False

    def test_reopen_open_period_rejected(self, service):
        """R-06: only LOCKED → OPEN; re-opening an OPEN period is refused."""
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        p2 = fy.period_for_date(date(2026, 2, 10))
        other = uuid4()
        with pytest.raises(PeriodTransitionError):
            svc.reopen_period(p2.id, other, "mở lại kỳ chưa khóa")

    def test_lock_closed_year_period_rejected(self, service):
        """A YEAR_CLOSED period must not be re-lockable — that would silently
        downgrade a closed year without the reopen SOD/approval flow."""
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        for p in fy.periods:
            svc.close_period(p.id, ACTOR, "khóa từng kỳ")
        svc.close_fiscal_year(COMPANY, fy.id, ACTOR)
        p1 = fy.period_for_date(date(2026, 1, 10))
        with pytest.raises(PeriodTransitionError):
            svc.close_period(p1.id, ACTOR, "khóa lại kỳ năm đã đóng")


class TestCloseFiscalYear:
    def test_s10_open_period_blocks_close(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        with pytest.raises(YearEndPreconditionsError):
            svc.close_fiscal_year(COMPANY, fy.id, ACTOR)

    def test_close_year_all_locked(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        for p in fy.periods:
            svc.close_period(p.id, ACTOR, "khóa từng kỳ")
        closed = svc.close_fiscal_year(COMPANY, fy.id, ACTOR)
        assert closed.status == PeriodStatus.YEAR_CLOSED
        assert closed.opening_balance_posted is True
        assert closed.closed_at is not None
        assert all(p.status == PeriodStatus.YEAR_CLOSED for p in closed.periods)

    def test_close_year_not_found(self, service):
        svc, fy_repo, _ = service
        with pytest.raises(NotFoundError):
            svc.close_fiscal_year(COMPANY, uuid4(), ACTOR)

    def test_close_year_twice_rejected(self, service):
        svc, fy_repo, _ = service
        fy = svc.ensure_fiscal_year(COMPANY, date(2026, 3, 15))
        for p in fy.periods:
            svc.close_period(p.id, ACTOR, "khóa từng kỳ")
        svc.close_fiscal_year(COMPANY, fy.id, ACTOR)
        with pytest.raises(PeriodTransitionError):
            svc.close_fiscal_year(COMPANY, fy.id, ACTOR)
