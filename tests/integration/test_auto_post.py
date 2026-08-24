"""Auto-post: posting an invoice generates + posts its journal voucher."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "55555555-5555-5555-5555-555555555555"


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


@pytest.fixture()
def chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
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
    coa.create_account(UUID(COMPANY), "112", "TG NH", actor=uuid4(), reason="c")
    coa.create_account(UUID(COMPANY), "1121", "TGNH", parent_code="112", actor=uuid4(), reason="c")
    coa.create_account(UUID(COMPANY), "131", "PTKH", actor=uuid4(), reason="c")
    coa.create_account(
        UUID(COMPANY), "1311", "PTKH chi tiết", parent_code="131", actor=uuid4(), reason="c"
    )
    coa.create_account(UUID(COMPANY), "5111", "DT BH", actor=uuid4(), reason="c")
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("HD/", "PT/"):
        ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")


INV = {
    "company_id": COMPANY,
    "customer_name": "KH A",
    "issue_date": "2026-08-05",
    "vat_rate": "0",  # keeps journal to two lines
    "items": [
        # Revenue line only — adapter generates the Nợ 1311 side
        {"account_code": "5111", "description": "rev", "amount": "10000000"},
    ],
}


class TestAutoPost:
    def test_post_creates_posted_voucher_with_matching_totals(self, chief, app, seeded):
        r = chief.post("/api/v1/invoices", json=INV)
        assert r.status_code == 201, r.get_json()
        inv = r.get_json()["data"]

        p = chief.post(f"/api/v1/invoices/{inv['id']}/post", json={"reason": "ok"})
        assert p.status_code == 200, p.get_json()
        body = p.get_json()["data"]
        assert body["status"] == "POSTED"
        assert body["voucher_number"] == "PT/000001"

        # Journal exists, balanced, POSTED, totals match invoice grand total
        v = chief.get(f"/api/v1/vouchers/{body['voucher_id']}")
        assert v.status_code == 200
        vdata = v.get_json()["data"]
        assert vdata["status"] == "POSTED"
        assert vdata["total_debit"] == vdata["total_credit"] == 10_000_000.0

    def test_double_invoice_post_does_not_duplicate_voucher(self, chief, seeded):
        r = chief.post("/api/v1/invoices", json={**INV, "customer_name": "KH B"})
        inv = r.get_json()["data"]
        chief.post(f"/api/v1/invoices/{inv['id']}/post", json={"reason": "1"})
        again = chief.post(f"/api/v1/invoices/{inv['id']}/post", json={"reason": "2"})
        assert again.status_code == 409
        lst = chief.get("/api/v1/vouchers", query_string={"company_id": COMPANY}).get_json()["data"]
        assert len(lst) == 1


class TestTT99AutoPost:
    """Seam 4: TT99 company end-to-end with 10-digit spec codes."""

    def test_journal_uses_template_codes_for_regime(self, monkeypatch):
        """Unit-level seam-4 proof: adapter honors injected template codes."""
        from datetime import date
        from decimal import Decimal

        from src.bricks.coa.domain import resolve_chart_role
        from src.bricks.invoice.domain import Invoice, InvoiceItem, InvoiceStatus
        from src.bricks.voucher.services import InvoiceServiceAdapter

        inv = Invoice(
            company_id=UUID(COMPANY),
            number="HD/000001",
            issue_date=date(2026, 8, 5),
            customer_name="X",
            items=[InvoiceItem("rev-placeholder", "d", Decimal(10000000))],
            vat_rate=Decimal(0),
        )
        inv.status = InvoiceStatus.POSTED
        codes = {role: resolve_chart_role(role, "tt99") for role in ("ar", "revenue", "vat_output")}
        lines = InvoiceServiceAdapter.lines_from_invoice(inv, codes)
        used = {l.account_code for l in lines}
        assert codes["ar"] in used and codes["revenue"] in used
        assert all(len(c) == 10 for c in used)
