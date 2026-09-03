"""Integration — B01/B02/B03 via ReportEngine + ledger source."""

from __future__ import annotations

from uuid import uuid4


def test_b01_returns_balanced_structure(admin_client, app):
    cid = uuid4()
    r = admin_client.get(f"/api/v1/reports/b01?company_id={cid}&year=2026&month=12")
    assert r.status_code == 200
    data = r.get_json()["data"]
    codes = {l["line_code"] for l in data}
    assert "A_TONG" in codes
    assert "TS_TONG" in codes
    assert "CHECK" in codes
    # empty ledger → all zeros → CHECK = 0
    check = next(l for l in data if l["line_code"] == "CHECK")
    assert check["value"] == 0.0


def test_b02_b03_require_auth(app):
    # no store entry → 401 via unauthorized_handler
    c = app.test_client()
    r = c.get(f"/api/v1/reports/b02?company_id={uuid4()}")
    assert r.status_code == 401


def test_close_month_needs_auth(app):
    c = app.test_client()
    r = c.post("/api/v1/reports/close-month", json={})
    assert r.status_code == 401
