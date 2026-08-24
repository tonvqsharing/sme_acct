"""Invoice API end-to-end: FY+COA+numbering+terms gates through real factory."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from src.app import create_app
from tests.integration.conftest import UUID_CHIEF, FakeUser, _store

SYS = "00000000-0000-0000-0000-000000000009"


@pytest.fixture()
def app():
    application = create_app(config={"TESTING": True, "SECRET_KEY": "x"})
    lm = application.login_manager

    @lm.user_loader
    def load(user_id):
        return _store.get(user_id)

    @lm.unauthorized_handler
    def unauth():
        return "", 401

    return application


@pytest.fixture()
def chief(app):
    user = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[user.id] = user
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = user.id
    return c


COMPANY = "22222222-2222-2222-2222-222222222222"


def _setup_company(svc_app):
    """FY year 2026 + COA accounts + HD/ series for COMPANY."""
    fy = svc_app.fy_service
    fy.create_year(
        COMPANY,
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor="00000000-0000-0000-0000-000000000003",
        reason="fy",
    )
    coa = svc_app.coa_service
    coa.create_account(COMPANY, "5111", "Doanh thu BH CC", actor=SYS, reason="coa")
    coa.create_account(COMPANY, "131", "Phải thu KH ngắn hạn", actor=SYS, reason="coa")
    coa.create_account(
        COMPANY,
        "1311",
        "Phải thu KH",
        parent_code="131",
        actor=SYS,
        reason="coa",
    )
    from src.bricks.payment_terms.web_adapter import (
        _series_service,
        _term_service,
    )

    assert _term_service() is not None
    _term_service().create_payment_term(
        company_id=UUID(COMPANY),
        name="Net 30",
        due_days=30,
        interest_rate=Decimal(0),
        actor="00000000-0000-0000-0000-000000000003",
        reason="terms",
        is_default=True,
    )
    assert _series_service is not None
    _series_service.create_series(
        company_id=UUID(COMPANY),
        prefix="HD/",
        actor="00000000-0000-0000-0000-000000000003",
        reason="series",
    )


BODY = {
    "company_id": COMPANY,
    "customer_name": "Công ty TNHH Khách",
    "issue_date": "2026-08-10",
    "vat_rate": "0.1",
    "items": [
        {"account_code": "5111", "description": "Bán hàng", "amount": "10000000"},
        {"account_code": "1311", "description": "Phải thu", "amount": "11000000"},
    ],
}


class TestInvoiceFlow:
    def test_full_hp004_flow(self, chief, app):
        _setup_company(app)
        r = chief.post("/api/v1/invoices", json=BODY)
        assert r.status_code == 201, r.get_json()
        data = r.get_json()["data"]
        assert data["number"] == "HD/000001"
        assert data["grand_total"] == 23_100_000.0
        assert data["due_date"] == "2026-09-09"
        assert data["status"] == "DRAFT"

        p = chief.post(
            f"/api/v1/invoices/{data['id']}/post",
            json={"reason": "approved"},
        )
        assert p.status_code == 200
        assert p.get_json()["data"]["status"] == "POSTED"

        again = chief.post(
            f"/api/v1/invoices/{data['id']}/post",
            json={"reason": "again"},
        )
        assert again.status_code == 409

    def test_closed_period_blocked(self, chief, app):
        _setup_company(app)
        from uuid import UUID as U

        fy = app.fy_service
        period = fy.find_open_period(U(COMPANY), date(2026, 8, 10))
        assert period is not None
        fy.close_period(period.id, actor=SYS, reason="close aug")
        r = chief.post("/api/v1/invoices", json=BODY)
        assert r.status_code == 409
        assert r.get_json()["code"] == "NO_OPEN_PERIOD"

    def test_bad_account_rejected(self, chief, app):
        _setup_company(app)
        bad = {**BODY, "items": [dict(BODY["items"][0], account_code="9999")]}
        r = chief.post("/api/v1/invoices", json=bad)
        assert r.status_code == 422

    def test_unauthenticated_401(self, app):
        resp = app.test_client().post("/api/v1/invoices", json=BODY)
        assert resp.status_code == 401
