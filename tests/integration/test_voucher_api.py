"""Voucher API — double-entry through real factory."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from tests.integration.conftest import (
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "33333333-3333-3333-3333-333333333333"
SYS = "00000000-0000-0000-0000-000000000009"


@pytest.fixture()
def chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def ready(app):
    app.fy_service.create_year(
        UUID(COMPANY),
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    coa.create_account(UUID(COMPANY), "112", "TG NH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "1121",
        "TGNH",
        parent_code="112",
        actor=uuid4(),
        reason="c",
    )
    coa.create_account(UUID(COMPANY), "5111", "Doanh thu BH", actor=uuid4(), reason="c")
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    ss.create_series(company_id=UUID(COMPANY), prefix="PT/", actor=uuid4(), reason="s")


BALANCED = {
    "company_id": COMPANY,
    "entry_date": "2026-08-12",
    "description": "Thu tiền KH",
    "lines": [
        {"account_code": "1121", "debit": "11000000", "credit": "0"},
        {"account_code": "5111", "debit": "0", "credit": "11000000"},
    ],
}


class TestVoucherApi:
    def test_create_and_post(self, chief, ready):
        r = chief.post("/api/v1/vouchers", json=BALANCED)
        assert r.status_code == 201, r.get_json()
        data = r.get_json()["data"]
        assert data["number"] == "PT/000001"

        p = chief.post(f"/api/v1/vouchers/{data['id']}/post", json={"reason": "ok"})
        assert p.status_code == 200
        assert p.get_json()["data"]["status"] == "POSTED"

        again = chief.post(f"/api/v1/vouchers/{data['id']}/post", json={"reason": "again"})
        assert again.status_code == 409

    def test_unbalanced_422_with_code(self, chief, ready):
        bad = {
            **BALANCED,
            "lines": [
                {"account_code": "1121", "debit": "100.02", "credit": "0"},
                {"account_code": "5111", "debit": "0", "credit": "100"},
            ],
        }
        r = chief.post("/api/v1/vouchers", json=bad)
        assert r.status_code == 422
        assert r.get_json()["code"] == "UNBALANCED_VOUCHER"

    def test_aggregate_account_rejected(self, chief, ready):
        bad = {
            **BALANCED,
            "lines": [
                {"account_code": "112", "debit": "5", "credit": "0"},
                {"account_code": "5111", "debit": "0", "credit": "5"},
            ],
        }
        r = chief.post("/api/v1/vouchers", json=bad)
        assert r.status_code == 422

    def test_closed_period_409(self, chief, app, ready):
        fy = app.fy_service
        period = fy.find_open_period(UUID(COMPANY), date(2026, 8, 12))
        fy.close_period(period.id, actor=uuid4(), reason="close aug")
        r = chief.post("/api/v1/vouchers", json=BALANCED)
        assert r.status_code == 409
        assert r.get_json()["code"] == "NO_OPEN_PERIOD"
