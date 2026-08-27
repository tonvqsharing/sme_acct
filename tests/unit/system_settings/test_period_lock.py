"""Unit tests for System Settings — period lock, config flags, legal review."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.bricks.system_settings.domain import (
    CompanyConfig,
    EInvoiceSeries,
)
from src.bricks.system_settings.services import (
    ConfigVersionConflictError,
    InvalidPeriodError,
    SystemSettingsService,
)


class FakePeriodLockRepo:
    """In-memory period lock repo for testing."""

    def __init__(self) -> None:
        self._locks: dict[tuple[str, int, int], dict] = {}

    def _key(self, cid, fy, p):
        return (str(cid), fy, p)

    def is_locked(self, cid, fy, p):
        return self._key(cid, fy, p) in self._locks

    def lock(self, cid, fy, p, actor, lock_type="PERIOD", notes=None):
        k = self._key(cid, fy, p)
        if k not in self._locks:
            self._locks[k] = {
                "fiscal_year": fy,
                "accounting_period": p,
                "lock_type": lock_type,
                "locked_by": str(actor),
                "notes": notes,
            }

    def unlock(self, cid, fy, p):
        k = self._key(cid, fy, p)
        if k in self._locks:
            del self._locks[k]
            return True
        return False

    def list_locked(self, cid, fy=None):
        return [
            v for (c, f, _), v in self._locks.items() if c == str(cid) and (fy is None or f == fy)
        ]


class FakeRepo:
    """In-memory repo for testing."""

    def __init__(self) -> None:
        self._configs: dict[str, CompanyConfig] = {}

    def get_config(self, cid):
        key = str(cid)
        if key not in self._configs:
            self._configs[key] = CompanyConfig(company_id=cid)
        return self._configs[key]

    def update_config(self, cfg):
        self._configs[str(cfg.company_id)] = cfg
        return cfg


class TestPeriodLock:
    def test_lock_and_check(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)
        actor = uuid4()

        assert not svc.is_period_locked(cid, 2026, 8)
        svc.lock_period(cid, 2026, 8, actor)
        assert svc.is_period_locked(cid, 2026, 8)

    def test_unlock(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)
        actor = uuid4()

        svc.lock_period(cid, 2026, 8, actor)
        assert svc.unlock_period(cid, 2026, 8)
        assert not svc.is_period_locked(cid, 2026, 8)

    def test_unlock_not_locked(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)

        assert not svc.unlock_period(cid, 2026, 8)

    def test_invalid_period_rejected(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)

        with pytest.raises(InvalidPeriodError):
            svc.lock_period(cid, 2026, 0, uuid4())
        with pytest.raises(InvalidPeriodError):
            svc.lock_period(cid, 2026, 13, uuid4())

    def test_list_locked_periods(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)
        actor = uuid4()

        svc.lock_period(cid, 2026, 1, actor)
        svc.lock_period(cid, 2026, 2, actor)
        svc.lock_period(cid, 2025, 12, actor)

        all_locked = svc.list_locked_periods(cid)
        assert len(all_locked) == 3

        fy_2026 = svc.list_locked_periods(cid, 2026)
        assert len(fy_2026) == 2

    def test_lock_idempotent(self):
        cid = uuid4()
        repo = FakeRepo()
        lock_repo = FakePeriodLockRepo()
        svc = SystemSettingsService(repo, lock_repo)
        actor = uuid4()

        svc.lock_period(cid, 2026, 8, actor)
        svc.lock_period(cid, 2026, 8, actor)  # No error
        assert svc.is_period_locked(cid, 2026, 8)


class TestConfigFlags:
    def test_update_config_flag(self):
        cid = uuid4()
        repo = FakeRepo()
        svc = SystemSettingsService(repo)
        actor = uuid4()

        cfg = svc.get_config(cid)
        assert cfg.fiscal_year_start_month == 1

        updated = svc.update_config_flag(
            cid, "fiscal_year_start_month", 4, actor, cfg.config_version
        )
        assert updated.fiscal_year_start_month == 4
        assert updated.config_version == cfg.config_version + 1

    def test_config_version_conflict(self):
        cid = uuid4()
        repo = FakeRepo()
        svc = SystemSettingsService(repo)
        actor = uuid4()

        cfg = svc.get_config(cid)
        # Simulate another writer
        svc.update_config_flag(cid, "fiscal_year_start_month", 4, actor, cfg.config_version)

        # Now try with old version
        with pytest.raises(ConfigVersionConflictError):
            svc.update_config_flag(cid, "fiscal_year_start_month", 7, actor, cfg.config_version)

    def test_unknown_flag_rejected(self):
        cid = uuid4()
        repo = FakeRepo()
        svc = SystemSettingsService(repo)

        with pytest.raises(ValueError):
            svc.update_config_flag(cid, "nonexistent_flag", "value", uuid4(), 0)


class TestLegalReview:
    def test_legal_review_stamp(self):
        cid = uuid4()
        repo = FakeRepo()
        svc = SystemSettingsService(repo)
        actor = uuid4()

        cfg = svc.get_config(cid)
        assert cfg.legal_reviewed_at is None

        reviewed = svc.legal_review(cid, actor)
        assert reviewed.legal_reviewed_by == actor
        assert reviewed.legal_reviewed_at is not None
        assert reviewed.config_version == cfg.config_version + 1


class TestDomainCompanyConfig:
    def test_with_series(self):
        cfg = CompanyConfig(company_id=uuid4())
        series = EInvoiceSeries(prefix="AA/2026")
        actor = uuid4()

        updated = cfg.with_series(series, actor)
        assert len(updated.e_invoice_series) == 1
        assert updated.config_version == 1

    def test_with_flag_update(self):
        cfg = CompanyConfig(company_id=uuid4())
        updated = cfg.with_flag_update("vat_settlement_cycle", "quarterly", uuid4())
        assert updated.vat_settlement_cycle == "quarterly"

    def test_with_legal_review(self):
        cfg = CompanyConfig(company_id=uuid4())
        now = datetime.now(UTC)
        reviewed = cfg.with_legal_review(uuid4(), now)
        assert reviewed.legal_reviewed_at == now
