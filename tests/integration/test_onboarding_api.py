"""Onboarding: create FY + chart accounts over HTTP — no service seeding."""

from __future__ import annotations

import typing
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_ADMIN,
    UUID_AUDITOR,
    FakeUser,
    _store,
)

COMPANY = "16161616-1616-1616-1616-161616161616"


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


class TestFiscalYearCreate:
    BODY: typing.ClassVar[dict[str, str]] = {
        "company_id": COMPANY,
        "name": "2026",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "period_frequency": "MONTHLY",
    }

    def test_admin_creates_year_with_periods(self, app):
        c = _client(app, UUID_ADMIN, "ADMIN")
        r = c.post("/api/v1/fiscal-years", json=self.BODY)
        assert r.status_code == 201, r.get_json()
        d = r.get_json()["data"]
        assert d["periods_count"] == 12
        # immediately usable: open-period lookup works
        fy_list = c.get("/api/v1/fiscal-years", query_string={"company_id": COMPANY}).get_json()[
            "data"
        ]
        assert len(fy_list) == 1

    def test_overlapping_year_409(self, app):
        c = _client(app, UUID_ADMIN, "ADMIN")
        c.post("/api/v1/fiscal-years", json=self.BODY)
        dup = {**self.BODY, "name": "dup", "start_date": "2026-07-01"}
        r = c.post("/api/v1/fiscal-years", json=dup)
        assert r.status_code == 409
        assert r.get_json()["code"] == "OVERLAPPING_YEAR"

    def test_auditor_cannot_create(self, app):
        c = _client(app, UUID_AUDITOR, "AUDITOR")
        assert c.post("/api/v1/fiscal-years", json=self.BODY).status_code == 403


class TestCoaWriteApi:
    def test_accountant_creates_aggregate_then_detail(self, accountant, app):
        r = accountant.post(
            "/api/v1/accounts",
            json={
                "company_id": COMPANY,
                "code": "131",
                "name": "Phải thu KH ngắn hạn",
            },
        )
        assert r.status_code == 201
        d = accountant.post(
            "/api/v1/accounts",
            json={
                "company_id": COMPANY,
                "code": "1311",
                "name": "PTKH chi tiết",
                "parent_code": "131",
            },
        )
        assert d.status_code == 201
        detail = d.get_json()["data"]
        assert detail["is_detail"] is True

    def test_duplicate_code_409(self, accountant, app):
        body = {"company_id": COMPANY, "code": "111", "name": "Tiền mặt"}
        accountant.post("/api/v1/accounts", json=body)
        r = accountant.post(
            "/api/v1/accounts",
            json={
                **body,
                "name": "Dup",
            },
        )
        assert r.status_code == 409
        assert r.get_json()["code"] == "DUPLICATE_ACCOUNT"

    def test_invalid_parent_422(self, accountant):
        r = accountant.post(
            "/api/v1/accounts",
            json={
                "company_id": COMPANY,
                "code": "1121",
                "name": "orphan",
                "parent_code": "112",
            },
        )
        assert r.status_code == 422

    def test_deactivate_chief_only(self, accountant, app):
        chief = _client(app, "00000000-0000-0000-0000-000000000003", "CHIEF_ACCOUNTANT")
        accountant.post(
            "/api/v1/accounts",
            json={
                "company_id": COMPANY,
                "code": "711",
                "name": "tmp",
            },
        )
        deny = accountant.post(
            "/api/v1/accounts/711/deactivate",
            json={
                "company_id": COMPANY,
                "reason": "no",
            },
        )
        assert deny.status_code == 403
        ok = chief.post(
            "/api/v1/accounts/711/deactivate",
            json={
                "company_id": COMPANY,
                "reason": "unused",
            },
        )
        assert ok.status_code == 200


class TestOnboardingEndToEnd:
    def test_new_company_can_post_first_invoice(self, app):
        """The full bootstrap an SME needs on day one."""
        admin = _client(app, UUID_ADMIN, "ADMIN")
        acc = _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")

        admin.post(
            "/api/v1/fiscal-years",
            json={
                "company_id": COMPANY,
                "name": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "period_frequency": "MONTHLY",
            },
        )
        admin.post("/api/v1/accounts", json={"company_id": COMPANY, "code": "511", "name": "DT"})
        admin.post(
            "/api/v1/accounts",
            json={"company_id": COMPANY, "code": "5111", "name": "BH", "parent_code": "511"},
        )
        admin.post("/api/v1/accounts", json={"company_id": COMPANY, "code": "333", "name": "Thue"})
        admin.post(
            "/api/v1/accounts",
            json={"company_id": COMPANY, "code": "3331", "name": "VAT ra", "parent_code": "333"},
        )

        from src.bricks.payment_terms.web_adapter import _series_service as ss

        ss.create_series(company_id=UUID(COMPANY), prefix="HD/", actor=uuid4(), reason="series")

        inv = acc.post(
            "/api/v1/invoices",
            json={
                "company_id": COMPANY,
                "customer_name": "Khach dau tien",
                "issue_date": "2026-09-01",
                "vat_rate": "0.08",
                "items": [
                    {"account_code": "5111", "description": "doanh thu", "amount": "1000000"}
                ],
                "reason": "first sale",
            },
        )
        assert inv.status_code == 201, inv.get_json()
