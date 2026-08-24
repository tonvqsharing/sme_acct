"""Bank & Cash API — contract + RBAC through real factory."""

from __future__ import annotations

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_AUDITOR,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "88888888-8888-8888-8888-888888888888"


@pytest.fixture()
def app():
    a = create_app(config={"TESTING": True, "SECRET_KEY": "x"})
    lm = a.login_manager

    @lm.user_loader
    def load(i):
        return _store.get(i)

    @lm.unauthorized_handler
    def un():
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


BANK = {
    "company_id": COMPANY,
    "bank_name": "VietinBank",
    "account_number": "1020100001234",
    "account_holder": "Công ty TNHH ABC",
    "branch": "Hà Nội",
}


class TestBankApi:
    def test_unauthenticated_401(self, app):
        assert app.test_client().post("/api/v1/bank-accounts", json=BANK).status_code == 401

    def test_auditor_write_blocked_403(self, app):
        c = _client(app, UUID_AUDITOR, "AUDITOR")
        assert c.post("/api/v1/bank-accounts", json=BANK).status_code == 403

    def test_accountant_create_then_duplicate_409(self, accountant):
        r = accountant.post("/api/v1/bank-accounts", json=BANK)
        assert r.status_code == 201
        d = r.get_json()["data"]
        assert len(d["checksum"]) == 64
        dup = accountant.post("/api/v1/bank-accounts", json=BANK)
        assert dup.status_code == 409
        assert dup.get_json()["code"] == "DUPLICATE_BANK_ACCOUNT"

    def test_set_primary_requires_chief(self, accountant, app):
        accountant.post("/api/v1/bank-accounts", json=BANK)
        second = accountant.post(
            "/api/v1/bank-accounts",
            json={**BANK, "account_number": "999"},
        ).get_json()["data"]
        denied = accountant.post(
            f"/api/v1/bank-accounts/{second['id']}/set-primary",
            json={"reason": "no"},
        )
        assert denied.status_code == 403
        ok = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT").post(
            f"/api/v1/bank-accounts/{second['id']}/set-primary",
            json={"reason": "chief switch"},
        )
        assert ok.status_code == 200
        assert ok.get_json()["data"]["is_primary"] is True


class TestCashApi:
    def test_create_and_adjust_flow(self, accountant):
        r = accountant.post(
            "/api/v1/cash-accounts",
            json={
                "company_id": COMPANY,
                "code": "111",
                "name": "Quỹ tổng",
                "opening_balance": "1000000",
                "reason": "init",
            },
        )
        assert r.status_code == 201
        cash = r.get_json()["data"]
        assert float(cash["current_balance"]) == 1_000_000.0

        adj = accountant.post(
            f"/api/v1/cash-accounts/{cash['id']}/adjust",
            json={"amount": "-400000", "reason": "chi tiền"},
        )
        assert adj.status_code == 200
        assert float(adj.get_json()["data"]["current_balance"]) == 600_000.0

    def test_negative_blocked_for_accountant_409(self, accountant):
        cash = accountant.post(
            "/api/v1/cash-accounts",
            json={
                "company_id": COMPANY,
                "code": "112",
                "name": "Q phụ",
                "opening_balance": "100",
                "reason": "i",
            },
        ).get_json()["data"]
        r = accountant.post(
            f"/api/v1/cash-accounts/{cash['id']}/adjust",
            json={"amount": "-500", "reason": "overdraw"},
        )
        assert r.status_code == 409
        assert r.get_json()["code"] == "NEGATIVE_BALANCE"

    def test_chief_may_overdraw(self, app):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        cash = chief.post(
            "/api/v1/cash-accounts",
            json={
                "company_id": COMPANY,
                "code": "113",
                "name": "Q TT58",
                "opening_balance": "100",
                "reason": "i",
            },
        ).get_json()["data"]
        r = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT").post(
            f"/api/v1/cash-accounts/{cash['id']}/adjust",
            json={"amount": "-300", "reason": "approved overdraft"},
        )
        assert r.status_code == 200

    def test_invalid_code_422(self, accountant):
        r = accountant.post(
            "/api/v1/cash-accounts",
            json={
                "company_id": COMPANY,
                "code": "0111",
                "name": "bad",
                "reason": "x",
            },
        )
        assert r.status_code == 422
