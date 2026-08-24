"""Purchase invoice API — EX-P01..P08 contract through real factory."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    UUID_AUDITOR,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "13131313-1313-1313-1313-131313131313"


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
def seeded(app):

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
    coa.create_account(UUID(COMPANY), "642", "Chi QLDN", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "6421",
        "Chi VP",
        parent_code="642",
        actor=uuid4(),
        reason="c",
    )


BODY = {
    "company_id": COMPANY,
    "supplier_name": "CTCP Hòa Bình",
    "supplier_mst": "0101234567",
    "invoice_number": "0001234",
    "invoice_symbol": "1C26TYY",
    "invoice_date": "2026-08-20",
    "entry_date": "2026-08-21",
    "payment_method": "bank",
    "payment_proof": True,
    "lines": [
        {
            "expense_account": "6421",
            "description": "Giấy A4",
            "amount_pre_vat": "2000000",
            "vat_rate": "0.1",
            "deductible": True,
        }
    ],
}


class TestPurchaseApi:
    def test_unauthenticated_401(self, app):
        assert app.test_client().post("/api/v1/purchase-invoices", json=BODY).status_code == 401

    def test_auditor_write_403(self, app):
        c = _client(app, UUID_AUDITOR, "AUDITOR")
        assert c.post("/api/v1/purchase-invoices", json=BODY).status_code == 403

    def test_happy_path_create_post(self, accountant, seeded):
        r = accountant.post("/api/v1/purchase-invoices", json=BODY)
        assert r.status_code == 201, r.get_json()
        d = r.get_json()["data"]
        assert d["status"] == "DRAFT"
        assert d["vat_deductible"] == 200000.0
        assert len(d["checksum"]) == 64

        p = accountant.post(f"/api/v1/purchase-invoices/{d['id']}/post", json={"reason": "ok"})
        assert p.status_code == 200
        assert p.get_json()["data"]["status"] == "POSTED"

    def test_duplicate_409_EX_P02(self, accountant, seeded):
        accountant.post("/api/v1/purchase-invoices", json=BODY)
        dup = accountant.post("/api/v1/purchase-invoices", json=BODY)
        assert dup.status_code == 409
        assert dup.get_json()["code"] == "DUPLICATE_INVOICE"

    def test_invalid_account_422_EX_P04(self, accountant, seeded):
        bad = {**BODY, "lines": [dict(BODY["lines"][0], expense_account="642")]}
        r = accountant.post("/api/v1/purchase-invoices", json=bad)
        assert r.status_code == 422
        assert r.get_json()["code"] == "INVALID_ACCOUNT"

    def test_total_mismatch_422(self, accountant, seeded):
        bad = {**BODY, "expected_total_payment": "999"}
        r = accountant.post("/api/v1/purchase-invoices", json=bad)
        assert r.status_code == 422
        assert r.get_json()["code"] == "TOTAL_MISMATCH"

    def test_cancel_requires_chief_then_soft(self, accountant, app, seeded):
        chief = _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")
        inv = accountant.post("/api/v1/purchase-invoices", json=BODY).get_json()["data"]
        accountant.post(f"/api/v1/purchase-invoices/{inv['id']}/post", json={"reason": "p"})

        denied = accountant.post(
            f"/api/v1/purchase-invoices/{inv['id']}/cancel", json={"reason": "no"}
        )
        assert denied.status_code == 403

        ok = chief.post(
            f"/api/v1/purchase-invoices/{inv['id']}/cancel",
            json={"reason": "sai sót NCC"},
        )
        assert ok.status_code == 200
        assert ok.get_json()["data"]["status"] == "CANCELLED"
