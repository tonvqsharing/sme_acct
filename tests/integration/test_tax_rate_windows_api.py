"""Tax-rate windows master-data API — SOD, overlap guard, date filter."""

from __future__ import annotations

from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_ADMIN,
    UUID_CHIEF,
    FakeUser,
    _store,
)

ADMIN = UUID_ADMIN
CHIEF = "00000000-0000-0000-0000-000000000003"


def _client(app, uid, role):
    u = FakeUser(uid, role)
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


class TestRateWindowsApi:
    def test_seeded_catalog_listed(self, app):
        c = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = c.get("/api/v1/tax-rate-windows")
        assert r.status_code == 200
        fracs = {x["fraction"] for x in r.get_json()["data"]}
        assert {"0", "0.05", "0.08", "0.1"} <= fracs

    def test_active_on_filter_hides_expired_8pct(self, app):
        c = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = c.get(
            "/api/v1/tax-rate-windows",
            query_string={"on": "2027-06-30"},
        ).get_json()["data"]
        assert all(x["fraction"] != "0.08" for x in r)
        r2 = c.get(
            "/api/v1/tax-rate-windows",
            query_string={"on": "2026-08-24"},
        ).get_json()["data"]
        assert any(x["fraction"] == "0.08" for x in r2)

    def test_accountant_cannot_add(self, app):
        c = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")
        r = c.post(
            "/api/v1/tax-rate-windows",
            json={
                "rate_pct": 8,
                "fraction": "0.08",
                "valid_from": "2027-01-01",
                "valid_to": "2027-12-31",
                "decree_ref": "NQ mới",
                "approver": CHIEF,
            },
        )
        assert r.status_code == 403

    def test_chief_adds_extension_window(self, app):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        # actor=chief; approver must differ → ADMIN id
        r = chief.post(
            "/api/v1/tax-rate-windows",
            json={
                "rate_pct": 8,
                "fraction": "0.08",
                "valid_from": "2027-01-01",
                "valid_to": "2027-06-30",
                "decree_ref": "NQ mới + NĐ mới 2026",
                "approver": ADMIN,
            },
        )
        assert r.status_code == 201, r.get_json()

        on = chief.get(
            "/api/v1/tax-rate-windows",
            query_string={"on": "2027-02-01"},
        ).get_json()["data"]
        assert any(x["fraction"] == "0.08" and x["active_on"] for x in on)

    def test_sod_self_approve_blocked_403(self, app):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        r = chief.post(
            "/api/v1/tax-rate-windows",
            json={
                "rate_pct": 8,
                "fraction": "0.08",
                "valid_from": "2028-01-01",
                "valid_to": None,
                "decree_ref": "self",
                "approver": CHIEF,
            },
        )
        assert r.status_code == 403
        assert r.get_json()["code"] == "SOD_VIOLATION"

    def test_overlap_rejected_409(self, app):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        r = chief.post(
            "/api/v1/tax-rate-windows",
            json={
                "rate_pct": 10,
                "fraction": "0.1",
                "valid_from": "2026-09-01",
                "valid_to": "2026-11-30",
                "decree_ref": "conflict",
                "approver": ADMIN,
            },
        )
        assert r.status_code == 409
        assert r.get_json()["code"] == "OVERLAPPING_WINDOW"
