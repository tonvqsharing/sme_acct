"""VAT declaration e2e — output from vouchers, input from purchases."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ACCOUNTANT,
    FakeUser,
    _store,
)

COMPANY = "15151515-1515-1515-1515-151515151515"


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


@pytest.fixture()
def accountant(app):
    u = FakeUser(UUID_ACCOUNTANT, "ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def seeded(app):
    fy = app.fy_service
    fy.create_year(
        UUID(COMPANY),
        "2026",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "MONTHLY",
        actor=uuid4(),
        reason="fy",
    )
    coa = app.coa_service
    for code in ("1111", "5111", "3331", "1331", "6421"):
        coa.create_account(UUID(COMPANY), code, code, actor=uuid4(), reason="c")
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("HD/", "PT/"):
        ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")


class TestVatDeclaration:
    def test_output_from_posted_sales_voucher(self, accountant, seeded):
        acc = accountant
        r = acc.post(
            "/api/v1/vouchers",
            json={
                "company_id": COMPANY,
                "entry_date": "2026-08-05",
                "description": "bán hàng",
                "lines": [
                    {"account_code": "1111", "debit": "11000000", "credit": "0"},
                    {"account_code": "5111", "debit": "0", "credit": "10000000"},
                    {"account_code": "3331", "debit": "0", "credit": "1000000"},
                ],
            },
        )
        assert r.status_code == 201
        vid = r.get_json()["data"]["id"]
        assert acc.post(f"/api/v1/vouchers/{vid}/post", json={"reason": "ok"}).status_code == 200

        q = {"company_id": COMPANY, "year": 2026, "month": 8}
        d = acc.get("/api/v1/reports/vat-declaration", query_string=q)
        assert d.status_code == 200
        data = d.get_json()["data"]
        assert data["output_vat"] == 1_000_000.0
        assert data["input_vat_deductible"] == 0.0
        assert data["vat_payable"] == 1_000_000.0

    def test_input_from_posted_purchase_offsets(self, accountant, seeded):
        # output first
        v = accountant.post(
            "/api/v1/vouchers",
            json={
                "company_id": COMPANY,
                "entry_date": "2026-08-05",
                "description": "out",
                "lines": [
                    {"account_code": "1111", "debit": "5500000", "credit": "0"},
                    {"account_code": "5111", "debit": "0", "credit": "5000000"},
                    {"account_code": "3331", "debit": "0", "credit": "500000"},
                ],
            },
        ).get_json()["data"]
        accountant.post(f"/api/v1/vouchers/{v['id']}/post", json={"reason": "x"})

        # purchase invoice: deductible VAT 200k
        pr = accountant.post(
            "/api/v1/purchase-invoices",
            json={
                "company_id": COMPANY,
                "supplier_name": "NCC VP",
                "supplier_mst": "0101234568",
                "invoice_number": "0002222",
                "invoice_symbol": "1C26TAA",
                "invoice_date": "2026-08-10",
                "entry_date": "2026-08-11",
                "payment_method": "bank",
                "payment_proof": True,
                "reason": "mua vp",
                "lines": [
                    {
                        "expense_account": "6421",
                        "description": "giấy",
                        "amount_pre_vat": "2000000",
                        "vat_rate": "0.1",
                        "deductible": True,
                    },
                ],
            },
        )
        assert pr.status_code == 201, pr.get_json()
        pid = pr.get_json()["data"]["id"]
        accountant.post(f"/api/v1/purchase-invoices/{pid}/post", json={"reason": "p"})

        d = accountant.get(
            "/api/v1/reports/vat-declaration",
            query_string={
                "company_id": COMPANY,
                "year": 2026,
                "month": 8,
            },
        ).get_json()["data"]
        assert d["output_vat"] == 500_000.0
        assert d["input_vat_deductible"] == 200_000.0
        assert d["vat_payable"] == 300_000.0

    def test_draft_voucher_excluded_R_V1(self, accountant, seeded):
        acc = accountant
        r = acc.post(
            "/api/v1/vouchers",
            json={
                "company_id": COMPANY,
                "entry_date": "2026-08-06",
                "description": "nháp",
                "lines": [
                    {"account_code": "3331", "debit": "0", "credit": "999"},
                    {"account_code": "5111", "debit": "999", "credit": "0"},
                ],
            },
        )
        vid = r.get_json()["data"]["id"]
        # NOT posted — must not appear
        d = acc.get(
            "/api/v1/reports/vat-declaration",
            query_string={
                "company_id": COMPANY,
                "year": 2026,
                "month": 8,
            },
        ).get_json()["data"]
        assert d["output_vat"] == 0.0
        assert acc.get(f"/api/v1/vouchers/{vid}").get_json()["data"]["status"] == "DRAFT"

    def test_unauthenticated_401(self, app):
        assert (
            app.test_client()
            .get(
                "/api/v1/reports/vat-declaration",
                query_string={"company_id": COMPANY, "year": 2026, "month": 8},
            )
            .status_code
            == 401
        )

    def test_bad_month_422(self, accountant, seeded):
        r = accountant.get(
            "/api/v1/reports/vat-declaration",
            query_string={
                "company_id": COMPANY,
                "year": 2026,
                "month": 13,
            },
        )
        assert r.status_code == 422
