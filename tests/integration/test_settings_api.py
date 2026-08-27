"""Integration tests for System Settings — period lock, config flags, legal review."""

from __future__ import annotations

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "19191919-1919-1919-1919-191919191919"


@pytest.fixture()
def app():
    a = create_app(config={"TESTING": True, "SECRET_KEY": "x"})
    lm = a.login_manager

    @lm.user_loader
    def load(i):
        return _store.get(i)

    @lm.unauthorized_handler
    def un():  # noqa: ANNO01
        return "", 401

    return a


def _client(app, uid, role):
    u = FakeUser(uid, role)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def accountant(app):
    return _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")


@pytest.fixture()
def chief(app):
    return _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")


class TestPeriodLockIntegration:
    def test_lock_period(self, accountant):
        """ACCOUNTANT can lock a period."""
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 8},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["locked"] is True

    def test_lock_period_with_notes(self, accountant):
        """Lock with notes."""
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 7, "notes": "Đã khóa tháng 7"},
        )
        assert r.status_code == 200

    def test_unlock_period_by_chief(self, chief):
        """CHIEF can unlock a period."""
        chief.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 6},
        )
        r = chief.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/unlock",
            json={"fiscal_year": 2026, "period": 6},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["unlocked"] is True

    def test_unlock_by_accountant_forbidden(self, accountant):
        """ACCOUNTANT cannot unlock (requires CHIEF)."""
        accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 5},
        )
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/unlock",
            json={"fiscal_year": 2026, "period": 5},
        )
        assert r.status_code == 403

    def test_period_status(self, accountant):
        """Get period lock status."""
        accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 1},
        )
        accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 2},
        )
        r = accountant.get(
            f"/api/v1/system-settings/config/{COMPANY}/period/status",
            query_string={"fiscal_year": 2026},
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert len(data) == 2

    def test_period_status_all_years(self, accountant):
        """Get all locked periods across years."""
        accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 1},
        )
        accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2025, "period": 12},
        )
        r = accountant.get(
            f"/api/v1/system-settings/config/{COMPANY}/period/status",
        )
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 2

    def test_invalid_period_rejected(self, accountant):
        """Invalid period number rejected."""
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 13},
        )
        assert r.status_code == 422

    def test_missing_body_rejected(self, accountant):
        """Missing required fields rejected."""
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={},
        )
        assert r.status_code == 422


class TestConfigFlagIntegration:
    def test_update_fiscal_year_start(self, accountant):
        """Update fiscal_year_start_month flag."""
        cfg_r = accountant.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        r = accountant.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 4, "config_version": version},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["config_version"] == version + 1

        # Verify
        cfg_r2 = accountant.get(f"/api/v1/system-settings/config/{COMPANY}")
        assert cfg_r2.get_json()["data"]["fiscal_year_start_month"] == 4

    def test_config_version_conflict(self, accountant):
        """Optimistic lock conflict returns 409."""
        cfg_r = accountant.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        # First update succeeds
        accountant.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 4, "config_version": version},
        )

        # Second update with old version fails
        r = accountant.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 7, "config_version": version},
        )
        assert r.status_code == 409

    def test_unknown_flag_rejected(self, accountant):
        """Unknown flag name rejected."""
        cfg_r = accountant.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        r = accountant.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/nonexistent",
            json={"value": "x", "config_version": version},
        )
        assert r.status_code == 422


class TestLegalReviewIntegration:
    def test_legal_review_by_chief(self, chief):
        """CHIEF_ACCOUNTANT can mark config as legally reviewed."""
        r = chief.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert data["legal_reviewed_at"] is not None
        assert data["legal_reviewed_by"] is not None

    def test_legal_review_by_accountant_forbidden(self, accountant):
        """ACCOUNTANT cannot do legal review."""
        r = accountant.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        assert r.status_code == 403

    def test_get_config_shows_legal_review(self, chief):
        """GET config shows legal review stamp."""
        chief.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        r = chief.get(f"/api/v1/system-settings/config/{COMPANY}")
        data = r.get_json()["data"]
        assert data["legal_reviewed_at"] is not None
