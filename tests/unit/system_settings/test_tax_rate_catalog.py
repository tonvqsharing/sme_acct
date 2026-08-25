"""Unit tests — TaxRateCatalogService (master-data governance)."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.bricks.system_settings.rate_windows import (
    SEED_TAX_RATE_WINDOWS,
    TaxRateWindow,
)
from src.bricks.system_settings.services import (
    SodViolationError,
    TaxRateCatalogService,
)

ADMIN = uuid4()
CHIEF = uuid4()


class _CatalogRepo:
    def __init__(self):
        self.rows = []

    def all(self):
        return list(self.rows)

    def add(self, w):
        self.rows.append(w)
        return w

    def remove(self, w):
        self.rows = [x for x in self.rows if x.id != w.id]
        return w

    def count(self):
        return len(self.rows)


@pytest.fixture()
def catalog_repo():
    return _CatalogRepo()


class FakeWindowsRepo:
    def __init__(self):
        self.rows: list[TaxRateWindow] = []

    def all(self):
        return list(self.rows)

    def add(self, window: TaxRateWindow) -> TaxRateWindow:
        self.rows.append(window)
        return window

    def count(self):
        return len(self.rows)


@pytest.fixture()
def svc():
    return TaxRateCatalogService(FakeWindowsRepo())


class TestSeeding:
    def test_ensure_seeded_inserts_lawful_set_once(self, svc):
        svc.ensure_seeded()
        svc.ensure_seeded()  # idempotent
        assert svc._repo.count() == len(SEED_TAX_RATE_WINDOWS)

    def test_seeded_windows_cover_aug_2026(self, svc):
        svc.ensure_seeded()
        fracs = svc.applicable_fractions(date(2026, 8, 24))
        assert fracs == frozenset({"0", "0.05", "0.08", "0.1"})

    def test_seeded_8pct_dies_at_sunset(self, svc):
        svc.ensure_seeded()
        assert "0.08" in svc.applicable_fractions(date(2026, 12, 31))
        assert "0.08" not in svc.applicable_fractions(date(2027, 1, 1))


class TestAddWindow:
    def _svc_seeded(self):
        s = TaxRateCatalogService(_CatalogRepo())
        s.ensure_seeded()
        return s

    def test_add_extension_window(self):
        s = self._svc_seeded()
        s.add_window(
            TaxRateWindow(8, "0.08", date(2027, 1, 1), date(2027, 6, 30), "NQ mới + NĐ mới"),
            actor=ADMIN,
            approver=CHIEF,
        )
        assert "0.08" in s.applicable_fractions(date(2027, 2, 1))

    def test_sod_approver_required(self):
        s = self._svc_seeded()
        with pytest.raises(SodViolationError):
            s.add_window(
                TaxRateWindow(8, "0.08", date(2027, 1, 1), None, "x"),
                actor=ADMIN,
                approver=ADMIN,
            )

    def test_overlapping_window_rejected(self):
        s = self._svc_seeded()
        with pytest.raises(ValueError, match="chồng lấn"):
            s.add_window(
                TaxRateWindow(10, "0.1", date(2026, 9, 1), date(2026, 11, 30), "conflict"),
                actor=ADMIN,
                approver=CHIEF,
            )

    def test_gate_uses_catalog_after_seed(self):
        """make_rate_gate over catalog rows == same behavior as constants."""
        from src.bricks.system_settings.rate_windows import make_rate_gate

        s = self._svc_seeded()
        gate = make_rate_gate(tuple(s._repo.all()))
        assert gate("0.08", date(2026, 8, 24)) is True
        with pytest.raises(ValueError, match="hết hiệu lực"):
            gate("0.08", date(2027, 1, 5))
