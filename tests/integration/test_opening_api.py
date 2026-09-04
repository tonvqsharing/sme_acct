"""Integration — opening batch S1: GL+bank → lock → voucher gate."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from tests.integration.conftest import (
    UUID_AUDITOR,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "99999999-9999-9999-9999-999999999999"


@pytest.fixture()
def chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def auditor(app):
    u = FakeUser(UUID_AUDITOR, "AUDITOR")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def ready(app):
    fy, _periods = app.fy_service.create_year(
        UUID(COMPANY),
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    coa.create_account(UUID(COMPANY), "111", "Tiền mặt", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY), "1111", "Tiền mặt VNĐ", parent_code="111", actor=uuid4(), reason="c"
    )
    coa.create_account(UUID(COMPANY), "411", "Vốn", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY), "4111", "Vốn góp", parent_code="411", actor=uuid4(), reason="c"
    )
    coa.create_account(UUID(COMPANY), "131", "PTKH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY), "1311", "PTKH ct", parent_code="131", actor=uuid4(), reason="c"
    )
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    ss.create_series(company_id=UUID(COMPANY), prefix="PT/", actor=uuid4(), reason="s")
    return {"fy_id": str(fy.id)}


VOUCHER = {
    "company_id": COMPANY,
    "entry_date": "2026-08-12",
    "description": "Thu tiền",
    "lines": [
        {"account_code": "1111", "debit": "100", "credit": "0"},
        {"account_code": "4111", "debit": "0", "credit": "100"},
    ],
}


class TestOpeningFlow:
    def test_full_s1_flow(self, chief, ready):
        fy_id = ready["fy_id"]
        r = chief.post(
            "/api/v1/opening-batches",
            json={"company_id": COMPANY, "fiscal_year_id": fy_id, "reason": "init"},
        )
        assert r.status_code == 201, r.get_json()
        bid = r.get_json()["data"]["id"]

        # live voucher blocked before lock
        blocked = chief.post("/api/v1/vouchers", json=VOUCHER)
        assert blocked.status_code == 409
        assert blocked.get_json()["code"] == "NO_OPENING_LOCK"

        # lock unbalanced → 409
        chief.post(
            f"/api/v1/opening-batches/{bid}/gl",
            json={
                "reason": "gl",
                "lines": [
                    {"account_code": "1111", "debit": "500", "credit": "0"},
                    {"account_code": "4111", "debit": "0", "credit": "400"},
                ],
            },
        )
        assert (
            chief.post(f"/api/v1/opening-batches/{bid}/lock", json={"reason": "go"}).status_code
            == 409
        )

        # fix via second GL post then lock (need fresh batch: locked-edit tested in unit)
        r2 = chief.post(
            "/api/v1/opening-batches",
            json={"company_id": COMPANY, "fiscal_year_id": fy_id, "reason": "init2"},
        )
        bid2 = r2.get_json()["data"]["id"]
        chief.post(
            f"/api/v1/opening-batches/{bid2}/gl",
            json={
                "reason": "gl",
                "lines": [
                    {"account_code": "1111", "debit": "500", "credit": "0"},
                    {"account_code": "4111", "debit": "0", "credit": "500"},
                ],
            },
        )
        chief.post(
            f"/api/v1/opening-batches/{bid2}/bank",
            json={
                "reason": "bank",
                "rows": [{"bank_account_id": str(uuid4()), "amount": "500"}],
            },
        )
        rep = chief.get(f"/api/v1/opening-batches/{bid2}/reconcile").get_json()["data"]
        assert rep["balanced"] is True
        assert rep["checks"]["bank_total"] == 500.0

        lock = chief.post(f"/api/v1/opening-batches/{bid2}/lock", json={"reason": "go-live"})
        assert lock.status_code == 200
        assert lock.get_json()["data"]["state"] == "LOCKED"

        # live voucher now allowed
        ok = chief.post("/api/v1/vouchers", json=VOUCHER)
        assert ok.status_code == 201, ok.get_json()

    def test_auditor_read_only(self, chief, auditor, ready):
        fy_id = ready["fy_id"]
        r = chief.post(
            "/api/v1/opening-batches",
            json={"company_id": COMPANY, "fiscal_year_id": fy_id, "reason": "init"},
        )
        assert r.status_code == 201
        denied = auditor.post(
            "/api/v1/opening-batches",
            json={"company_id": COMPANY, "fiscal_year_id": fy_id, "reason": "x"},
        )
        assert denied.status_code == 403
        assert (
            auditor.get(
                f"/api/v1/opening-batches/{r.get_json()['data']['id']}/reconcile"
            ).status_code
            == 200
        )


class TestCounterpartyFlow:
    def test_counterparty_tie_and_aging(self, chief, ready):
        fy_id = ready["fy_id"]
        p = chief.post(
            "/api/v1/parties",
            json={
                "company_id": COMPANY,
                "code": "KH-001",
                "name": "Khách A",
                "mst": "0101234567",
                "is_customer": True,
            },
        )
        assert p.status_code == 201, p.get_json()
        pid = p.get_json()["data"]["id"]

        r = chief.post(
            "/api/v1/opening-batches",
            json={"company_id": COMPANY, "fiscal_year_id": fy_id, "reason": "init"},
        )
        bid = r.get_json()["data"]["id"]
        cp = chief.post(
            f"/api/v1/opening-batches/{bid}/counterparties",
            json={
                "reason": "ar",
                "rows": [
                    {
                        "account_code": "1311",
                        "party_id": pid,
                        "side": "debit",
                        "amount": "200",
                    }
                ],
            },
        )
        assert cp.status_code == 201, cp.get_json()

        # GL must tie or lock fails
        chief.post(
            f"/api/v1/opening-batches/{bid}/gl",
            json={
                "reason": "gl",
                "lines": [
                    {"account_code": "1311", "debit": "200", "credit": "0"},
                    {"account_code": "4111", "debit": "0", "credit": "200"},
                ],
            },
        )
        # need 4111 aggregate? use detail accounts instead
        lock = chief.post(f"/api/v1/opening-batches/{bid}/lock", json={"reason": "go"})
        assert lock.status_code == 200, lock.get_json()

        aging = chief.get(
            "/api/v1/reports/ar-aging",
            query_string={"company_id": COMPANY, "as_of": "2026-08-31"},
        )
        buckets = {x["bucket"]: x["amount"] for x in aging.get_json()["data"]}
        assert buckets["current"] == 200.0
