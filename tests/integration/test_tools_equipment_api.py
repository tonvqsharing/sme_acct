"""Tools & Equipment (CCDC) integration tests — real create_app + SQLite."""

from __future__ import annotations

from uuid import UUID

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_AUDITOR,
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
    u.company_id = UUID(COMPANY)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
    """Seed COA accounts needed for CCDC."""
    from uuid import uuid4 as _u

    app.coa_service.create_account(UUID(COMPANY), "642", "Chi QLDN", actor=_u(), reason="c")
    app.coa_service.create_account(
        UUID(COMPANY), "242", "Chi phi tra truoc", actor=_u(), reason="c"
    )


@pytest.fixture()
def accountant(app, seeded):
    return _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")


@pytest.fixture()
def chief(app, seeded):
    return _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")


@pytest.fixture()
def auditor(app, seeded):
    return _client(app, UUID_AUDITOR, "AUDITOR")


BODY = {
    "code": "LPT-001",
    "name": "Laptop Dell Inspiron 15",
    "category": "Thiết bị văn phòng",
    "purchase_date": "2026-08-15",
    "purchase_price": 15000000,
    "useful_life_months": 12,
    "expense_account_code": "642",
    "prepaid_account_code": "242",
}


class TestCCDCIntegration:
    """Integration tests for CCDC CRUD + allocation."""

    def test_create_and_get_roundtrip(self, accountant):
        """Create CCDC → get by ID → verify fields."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        assert r.status_code == 201, r.get_json()
        d = r.get_json()["data"]
        assert d["code"] == "LPT-001"
        assert d["status"] == "Active"
        assert d["monthly_allocation"] == "1250000"

        g = accountant.get(f"/api/v1/tools-equipment/{d['id']}")
        assert g.status_code == 200
        assert g.get_json()["data"]["code"] == "LPT-001"

    def test_list_ccdc(self, accountant):
        """List CCDC returns empty initially, then returns items."""
        r = accountant.get("/api/v1/tools-equipment")
        assert r.status_code == 200
        assert r.get_json()["data"] == []

        accountant.post("/api/v1/tools-equipment", json=BODY)
        r = accountant.get("/api/v1/tools-equipment")
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 1

    def test_update_ccdc(self, accountant):
        """Update CCDC name and verify change."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        u = accountant.patch(
            f"/api/v1/tools-equipment/{ccdc_id}",
            json={"name": "Laptop Dell XPS 15"},
        )
        assert u.status_code == 200
        assert u.get_json()["data"]["name"] == "Laptop Dell XPS 15"

    def test_update_rejects_price_zero(self, accountant):
        """Update with invalid price triggers domain validation."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        u = accountant.patch(
            f"/api/v1/tools-equipment/{ccdc_id}",
            json={"purchase_price": 0},
        )
        assert u.status_code == 400

    def test_deactivate_by_chief(self, accountant, chief):
        """CHIEF_ACCOUNTANT can deactivate ACTIVE CCDC."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        d = chief.post(f"/api/v1/tools-equipment/{ccdc_id}/deactivate")
        assert d.status_code == 200
        assert d.get_json()["data"]["status"] == "Inactive"

    def test_deactivate_by_accountant_forbidden(self, accountant):
        """ACCOUNTANT cannot deactivate CCDC (requires CHIEF)."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        d = accountant.post(f"/api/v1/tools-equipment/{ccdc_id}/deactivate")
        assert d.status_code == 403

    def test_reactivate_by_chief(self, accountant, chief):
        """CHIEF_ACCOUNTANT can reactivate INACTIVE CCDC."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        chief.post(f"/api/v1/tools-equipment/{ccdc_id}/deactivate")
        react = chief.post(f"/api/v1/tools-equipment/{ccdc_id}/reactivate")
        assert react.status_code == 200
        assert react.get_json()["data"]["status"] == "Active"

    def test_write_off_by_chief(self, accountant, chief):
        """CHIEF_ACCOUNTANT can write off CCDC."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        w = chief.post(f"/api/v1/tools-equipment/{ccdc_id}/write-off")
        assert w.status_code == 200
        assert w.get_json()["data"]["status"] == "WrittenOff"

    def test_write_off_by_accountant_forbidden(self, accountant):
        """ACCOUNTANT cannot write off CCDC (requires CHIEF)."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        w = accountant.post(f"/api/v1/tools-equipment/{ccdc_id}/write-off")
        assert w.status_code == 403

    def test_auditor_read_only(self, auditor):
        """AUDITOR can read but not create CCDC."""
        r = auditor.post("/api/v1/tools-equipment", json=BODY)
        assert r.status_code == 403

        g = auditor.get("/api/v1/tools-equipment")
        assert g.status_code == 200

    def test_unauthenticated_returns_401(self, app):
        """Unauthenticated request returns 401."""
        c = app.test_client()
        r = c.get("/api/v1/tools-equipment")
        assert r.status_code == 401

    def test_list_allocations_scoped(self, accountant):
        """list_allocations verifies CCDC belongs to company."""
        r = accountant.post("/api/v1/tools-equipment", json=BODY)
        ccdc_id = r.get_json()["data"]["id"]

        # List allocations for existing CCDC
        la = accountant.get(f"/api/v1/tools-equipment/{ccdc_id}/allocations")
        assert la.status_code == 200

        # Non-existent CCDC returns 404
        from uuid import uuid4

        la2 = accountant.get(f"/api/v1/tools-equipment/{uuid4()}/allocations")
        assert la2.status_code == 404
