"""Fiscal year & period brick — unit tests (fake repo)."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.bricks.fiscal_year_period.services import (
    FiscalYearService,
    OverlappingYearError,
    PeriodNotFoundError,
    PeriodStatus,
    YearNotFoundError,
)
from src.bricks.fiscal_year_period.storage import FiscalYear, Period

COMPANY = uuid4()


class FakeFYRepo:
    def __init__(self):
        self.years: dict[UUID, FiscalYear] = {}

    def create(self, fy):
        self.years[fy.id] = fy
        return fy

    def get_by_id(self, fy_id):
        return self.years.get(fy_id)

    def get_by_company(self, company_id):
        return [y for y in self.years.values() if y.company_id == company_id]

    def update(self, fy):
        self.years[fy.id] = fy
        return fy


class FakePeriodRepo:
    def __init__(self):
        self.periods: dict[UUID, Period] = {}

    def create_many(self, periods):
        for p in periods:
            self.periods[p.id] = p
        return list(periods)

    def get_by_id(self, period_id):
        return self.periods.get(period_id)

    def get_by_year(self, fiscal_year_id):
        return [p for p in self.periods.values() if p.fiscal_year_id == fiscal_year_id]

    def find_by_date(self, company_id, on_date):
        for p in self.periods.values():
            if p.company_id == company_id and p.start_date <= on_date <= p.end_date:
                return p
        return None

    def update(self, period):
        self.periods[period.id] = period
        return period


@pytest.fixture()
def deps():
    fy_repo, period_repo = FakeFYRepo(), FakePeriodRepo()
    svc = FiscalYearService(fy_repo, period_repo)
    return svc, fy_repo, period_repo


class TestCreateYear:
    def test_creates_year_with_12_monthly_periods(self, deps):
        svc, _, _period_repo = deps
        _fy, periods = svc.create_year(
            company_id=COMPANY,
            name="2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            period_frequency="MONTHLY",
            actor=uuid4(),
            reason="init",
        )
        assert len(periods) == 12
        assert periods[0].start_date == date(2026, 1, 1)
        assert periods[-1].end_date == date(2026, 12, 31)
        assert all(p.status == PeriodStatus.OPEN for p in periods)

    def test_overlapping_year_rejected(self, deps):
        svc, _, _ = deps
        svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        with pytest.raises(OverlappingYearError):
            svc.create_year(
                COMPANY,
                "Overlap",
                date(2026, 7, 1),
                date(2027, 6, 30),
                "MONTHLY",
                actor=uuid4(),
                reason="r",
            )

    def test_same_dates_ok_for_other_company(self, deps):
        svc, _, _ = deps
        svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        other = uuid4()
        fy, _ = svc.create_year(
            other,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        assert fy.company_id == other


class TestCloseReopen:
    def test_close_period_then_find_by_date_returns_none(self, deps):
        svc, _, _period_repo = deps
        _, periods = svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        jan = periods[0]
        svc.close_period(jan.id, actor=uuid4(), reason="month end")
        assert svc.find_open_period(COMPANY, date(2026, 1, 15)) is None
        # Feb still open
        found = svc.find_open_period(COMPANY, date(2026, 2, 15))
        assert found is not None

    def test_reopen_period(self, deps):
        svc, _, _period_repo = deps
        _, periods = svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        jan = periods[0]
        svc.close_period(jan.id, actor=uuid4(), reason="close")
        svc.reopen_period(jan.id, actor=uuid4(), reason="late invoice")
        assert svc.find_open_period(COMPANY, date(2026, 1, 15)) is not None

    def test_close_unknown_period_raises(self, deps):
        svc, _, _ = deps
        with pytest.raises(PeriodNotFoundError):
            svc.close_period(uuid4(), actor=uuid4(), reason="ghost")


class TestFindForPosting:
    def test_open_period_lookup(self, deps):
        svc, _, _period_repo = deps
        svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        period = svc.find_open_period(COMPANY, date(2026, 5, 20))
        assert period is not None
        assert period.start_date == date(2026, 5, 1)

    def test_before_any_year_returns_none(self, deps):
        svc, _, _ = deps
        assert svc.find_open_period(COMPANY, date(2000, 1, 1)) is None


class TestYearClose:
    def test_close_year_closes_all_periods(self, deps):
        svc, fy_repo, period_repo = deps
        fy, _ = svc.create_year(
            COMPANY,
            "2026",
            date(2026, 1, 1),
            date(2026, 12, 31),
            "MONTHLY",
            actor=uuid4(),
            reason="r",
        )
        svc.close_year(fy.id, actor=uuid4(), reason="year end")
        stored = fy_repo.get_by_id(fy.id)
        assert stored.status.value == "YEAR_CLOSED"
        assert all(p.status == PeriodStatus.CLOSED for p in period_repo.get_by_year(fy.id))

    def test_cannot_close_missing_year(self, deps):
        svc, _, _ = deps
        with pytest.raises(YearNotFoundError):
            svc.close_year(uuid4(), actor=uuid4(), reason="x")
