"""Integration tests for System Settings — period lock, config flags, legal review."""

from __future__ import annotations

COMPANY = "19191919-1919-1919-1919-191919191919"


class TestPeriodLockIntegration:
    def test_lock_period(self, accountant_client):
        """ACCOUNTANT can lock a period."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 8},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["locked"] is True

    def test_lock_period_with_notes(self, accountant_client):
        """Lock with notes."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 7, "notes": "Đã khóa tháng 7"},
        )
        assert r.status_code == 200

    def test_unlock_period_by_chief(self, chief_client):
        """CHIEF can unlock a period."""
        chief_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 6},
        )
        r = chief_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/unlock",
            json={"fiscal_year": 2026, "period": 6},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["unlocked"] is True

    def test_unlock_by_accountant_forbidden(self, accountant_client):
        """ACCOUNTANT cannot unlock (requires CHIEF)."""
        accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 5},
        )
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/unlock",
            json={"fiscal_year": 2026, "period": 5},
        )
        assert r.status_code == 403

    def test_period_status(self, accountant_client):
        """Get period lock status."""
        accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 1},
        )
        accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 2},
        )
        r = accountant_client.get(
            f"/api/v1/system-settings/config/{COMPANY}/period/status",
            query_string={"fiscal_year": 2026},
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert len(data) == 2

    def test_period_status_all_years(self, accountant_client):
        """Get all locked periods across years."""
        accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 1},
        )
        accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2025, "period": 12},
        )
        r = accountant_client.get(
            f"/api/v1/system-settings/config/{COMPANY}/period/status",
        )
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 2

    def test_invalid_period_rejected(self, accountant_client):
        """Invalid period number rejected."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": 2026, "period": 13},
        )
        assert r.status_code == 422

    def test_missing_body_rejected(self, accountant_client):
        """Missing required fields rejected."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={},
        )
        assert r.status_code == 422

    def test_negative_fiscal_year_rejected(self, accountant_client):
        """Negative fiscal year rejected."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": -1, "period": 1},
        )
        assert r.status_code == 422

    def test_bad_fiscal_year_type_rejected(self, accountant_client):
        """Non-integer fiscal year rejected."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/period/lock",
            json={"fiscal_year": "abc", "period": 1},
        )
        assert r.status_code == 422


class TestConfigFlagIntegration:
    def test_update_fiscal_year_start(self, accountant_client):
        """Update fiscal_year_start_month flag."""
        cfg_r = accountant_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        r = accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 4, "config_version": version},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["config_version"] == version + 1

        # Verify
        cfg_r2 = accountant_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        assert cfg_r2.get_json()["data"]["fiscal_year_start_month"] == 4

    def test_config_version_conflict(self, accountant_client):
        """Optimistic lock conflict returns 409."""
        cfg_r = accountant_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        # First update succeeds
        accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 4, "config_version": version},
        )

        # Second update with old version fails
        r = accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 7, "config_version": version},
        )
        assert r.status_code == 409

    def test_unknown_flag_rejected(self, accountant_client):
        """Unknown flag name rejected."""
        cfg_r = accountant_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        r = accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/nonexistent",
            json={"value": "x", "config_version": version},
        )
        assert r.status_code == 422

    def test_invalid_flag_value_rejected(self, accountant_client):
        """Invalid flag value rejected."""
        cfg_r = accountant_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        version = cfg_r.get_json()["data"]["config_version"]

        r = accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 99, "config_version": version},
        )
        assert r.status_code == 422

    def test_bad_config_version_type_rejected(self, accountant_client):
        """Non-integer config_version rejected."""
        r = accountant_client.patch(
            f"/api/v1/system-settings/config/{COMPANY}/flags/fiscal_year_start_month",
            json={"value": 4, "config_version": "abc"},
        )
        assert r.status_code == 422


class TestLegalReviewIntegration:
    def test_legal_review_by_chief(self, chief_client):
        """CHIEF_ACCOUNTANT can mark config as legally reviewed."""
        r = chief_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert data["legal_reviewed_at"] is not None
        assert data["legal_reviewed_by"] is not None

    def test_legal_review_by_accountant_forbidden(self, accountant_client):
        """ACCOUNTANT cannot do legal review."""
        r = accountant_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        assert r.status_code == 403

    def test_get_config_shows_legal_review(self, chief_client):
        """GET config shows legal review stamp."""
        chief_client.post(
            f"/api/v1/system-settings/config/{COMPANY}/legal-review",
        )
        r = chief_client.get(f"/api/v1/system-settings/config/{COMPANY}")
        data = r.get_json()["data"]
        assert data["legal_reviewed_at"] is not None
