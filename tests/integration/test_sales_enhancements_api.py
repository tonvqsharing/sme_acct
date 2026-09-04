"""Integration — sales enhancements end-to-end via real factory."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest

from tests.integration.conftest import UUID_AUDITOR, UUID_CHIEF, FakeUser, _store

COMPANY = "66666666-6666-6666-6666-666666666666"
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
def auditor(app):
    u = FakeUser(UUID_AUDITOR, "AUDITOR")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
    from uuid import uuid4 as _u

    app.fy_service.create_year(
        UUID(COMPANY),
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=_u(),
        reason="fy",
    )
    coa = app.coa_service
    # base COA
    for code, name, parent in [
        ("131", "PTKH", None),
        ("1311", "PTKH ct", "131"),
        ("511", "DT", None),
        ("5111", "DT BH", "511"),
        ("333", "Thue", None),
        ("3331", "GTGT ra", "333"),
        ("521", "Giam tru DT", None),
        ("5211", "Chiet khau", "521"),
        ("5212", "Hang tra lai", "521"),
        ("5213", "Giam gia", "521"),
        ("3387", "DT chua thuc hien", None),
    ]:
        try:
            coa.create_account(
                UUID(COMPANY), code, name, parent_code=parent, actor=_u(), reason="c"
            )
        except Exception:  # noqa: BLE001, S110
            pass
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("HD/", "PT/"):
        try:
            ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=_u(), reason="s")
        except Exception:  # noqa: BLE001, S110
            pass
    # ensure payment term
    from src.bricks.payment_terms.web_adapter import _term_service

    try:
        _term_service().create_payment_term(
            company_id=UUID(COMPANY),
            name="Net 30",
            due_days=30,
            actor=_u(),
            reason="t",
            is_default=True,
            interest_rate=0,  # type: ignore[call-arg]  # compat
        )
    except Exception:  # noqa: BLE001, S110
        pass


def _create_invoice_payload(**over):
    base = {
        "company_id": COMPANY,
        "customer_name": "KH A",
        "issue_date": "2026-08-10",
        "items": [
            {"account_code": "5111", "description": "hang", "amount": "10000000", "vat_rate": "0.1"}
        ],
    }
    base.update(over)
    return base


class TestMixedVAT:
    def test_mixed_rates_post_and_journal(self, chief, seeded):
        payload = _create_invoice_payload(
            items=[
                {
                    "account_code": "5111",
                    "amount": "10000000",
                    "vat_rate": "0.05",
                    "description": "sach",
                },
                {
                    "account_code": "5111",
                    "amount": "20000000",
                    "vat_rate": "0.10",
                    "description": "tu van",
                },
                {
                    "account_code": "5111",
                    "amount": "5000000",
                    "vat_rate": "0.08",
                    "category": "manufacturing",
                    "description": "sx",
                },
            ]
        )
        r = chief.post("/api/v1/invoices", json=payload)
        assert r.status_code == 201, r.get_json()
        data = r.get_json()["data"]
        assert data["vat_breakdown"]["0.05"] == 500000.0
        assert data["vat_breakdown"]["0.08"] == 400000.0
        p = chief.post(f"/api/v1/invoices/{data['id']}/post", json={"reason": "ok"})
        assert p.status_code == 200
        # ledger check: trial_balance reflects posted
        tb = chief.get(
            "/api/v1/reports/trial-balance",
            query_string={"company_id": COMPANY, "from": "2026-08-01", "to": "2026-08-31"},
        )
        assert tb.status_code == 200
        assert tb.get_json()["totals"]["debit"] == tb.get_json()["totals"]["credit"]


class TestFX:
    def test_fx_invoice(self, chief, seeded):
        payload = _create_invoice_payload(
            currency_code="USD",
            fx_rate="25400",
            items=[{"account_code": "5111", "amount": "1000000", "vat_rate": "0.0"}],
        )
        r = chief.post("/api/v1/invoices", json=payload)
        assert r.status_code == 201, r.get_json()
        assert r.get_json()["data"]["currency_code"] == "USD"
        assert r.get_json()["data"]["fx_rate"] == 25400.0


class TestRBAC:
    def test_auditor_cannot_create_or_post(self, auditor, seeded):
        payload = _create_invoice_payload()
        r = auditor.post("/api/v1/invoices", json=payload)
        assert r.status_code == 403
        assert r.get_json()["code"] == "SOD_VIOLATION"


class TestDeduction:
    def test_deduction_happy(self, chief, seeded):
        payload = _create_invoice_payload()
        r = chief.post("/api/v1/invoices", json=payload)
        inv_id = r.get_json()["data"]["id"]
        chief.post(f"/api/v1/invoices/{inv_id}/post", json={"reason": "ok"})
        d = chief.post(
            f"/api/v1/invoices/{inv_id}/deduction",
            json={"deduction_type": "RETURN", "amount": "5000000", "reason": "tra hang"},
        )
        assert d.status_code == 201, d.get_json()
        assert d.get_json()["data"]["total_debit"] == 5000000.0
        # For brevity just check deduction type validation
        bad = chief.post(
            f"/api/v1/invoices/{inv_id}/deduction",
            json={"deduction_type": "BAD", "amount": "100", "reason": "x"},
        )
        assert bad.status_code == 422


def _enable_einvoice(chief):
    cfg = chief.get(f"/api/v1/system-settings/config/{COMPANY}").get_json()["data"]
    r = chief.patch(
        f"/api/v1/system-settings/config/{COMPANY}/flags/sales_einvoice_enabled",
        json={"value": True, "config_version": cfg["config_version"]},
    )
    assert r.status_code == 200, r.get_json()


class TestEInvoice:
    def test_issue_mock(self, chief, seeded):
        _enable_einvoice(chief)
        payload = _create_invoice_payload(template_code="1C26TAA", invoice_symbol="HD/")
        r = chief.post("/api/v1/invoices", json=payload)
        inv_id = r.get_json()["data"]["id"]
        chief.post(f"/api/v1/invoices/{inv_id}/post", json={"reason": "ok"})
        iss = chief.post(f"/api/v1/invoices/{inv_id}/einvoice/issue", json={"reason": "phat hanh"})
        assert iss.status_code == 200, iss.get_json()
        assert iss.get_json()["data"]["einvoice_status"] == "SENT"
        # double issue → 409
        again = chief.post(f"/api/v1/invoices/{inv_id}/einvoice/issue", json={"reason": "again"})
        assert again.status_code == 409

    def test_issue_requires_posted(self, chief, seeded):
        _enable_einvoice(chief)
        payload = _create_invoice_payload(template_code="1C26TAA", invoice_symbol="HD/")
        r = chief.post("/api/v1/invoices", json=payload)
        inv_id = r.get_json()["data"]["id"]
        iss = chief.post(f"/api/v1/invoices/{inv_id}/einvoice/issue", json={})
        assert iss.status_code == 422

    def test_issue_blocked_when_flag_off(self, chief, seeded):
        payload = _create_invoice_payload(template_code="1C26TAA", invoice_symbol="HD/")
        r = chief.post("/api/v1/invoices", json=payload)
        inv_id = r.get_json()["data"]["id"]
        chief.post(f"/api/v1/invoices/{inv_id}/post", json={"reason": "ok"})
        iss = chief.post(f"/api/v1/invoices/{inv_id}/einvoice/issue", json={})
        assert iss.status_code == 403
        assert iss.get_json()["code"] == "E_INVOICE_DISABLED"


class TestLedgerPaginationAndAging:
    def test_pagination(self, chief, seeded):
        # create 3 invoices
        for i in range(3):
            payload = _create_invoice_payload(customer_name=f"KH {i}")
            r = chief.post("/api/v1/invoices", json=payload)
            chief.post(f"/api/v1/invoices/{r.get_json()['data']['id']}/post", json={"reason": "ok"})
        gj = chief.get(
            "/api/v1/reports/general-journal",
            query_string={
                "company_id": COMPANY,
                "from": "2026-08-01",
                "to": "2026-08-31",
                "page": 1,
                "page_size": 2,
            },
        )
        assert gj.status_code == 200
        assert len(gj.get_json()["data"]) <= 2
        aging = chief.get(
            "/api/v1/reports/ar-aging", query_string={"company_id": COMPANY, "as_of": "2026-08-31"}
        )
        assert aging.status_code == 200
        assert "data" in aging.get_json()
