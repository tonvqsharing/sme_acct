"""TT99 end-to-end: 10-digit chart through invoice → auto-journal → reports."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_ADMIN,
    UUID_CHIEF,
    FakeUser,
    _store,
)

COMPANY = "77777777-7777-7777-7777-777777777777"


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
def chief(app):
    u = FakeUser(UUID_CHIEF, "CHIEF_ACCOUNTANT")
    _store[u.id] = u
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = u.id
    return c


@pytest.fixture()
def tt99_company(app):
    """Real company row pinned to the TT99 regime."""
    from src.bricks.company.domain import AccountingRegime, CompanyType
    from src.bricks.company.web_adapter import _company_service as cs

    return cs.create(
        legal_name="CTCP TNHH TT99",
        mst="0987654321",
        company_type=CompanyType.MULTI_LLC,
        accounting_regime=AccountingRegime.TT99,
        created_by=UUID(UUID_ADMIN),
    )


@pytest.fixture()
def seeded(app, tt99_company):
    COMPANY = str(tt99_company.id)  # align seeds with the real company row
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
    R = "tt99"
    # aggregates then posting leaves — 10-digit spec codes
    coa.create_account(
        UUID(COMPANY), "1310000000", "Phải thu KH", regime=R, actor=uuid4(), reason="c"
    )
    coa.create_account(
        UUID(COMPANY),
        "1311000001",
        "KH A",
        parent_code="1310000000",
        regime=R,
        actor=uuid4(),
        reason="c",
    )
    coa.create_account(
        UUID(COMPANY), "5110000000", "Doanh thu BH", regime=R, actor=uuid4(), reason="c"
    )
    coa.create_account(
        UUID(COMPANY),
        "5111000001",
        "BH hàng chính",
        parent_code="5110000000",
        regime=R,
        actor=uuid4(),
        reason="c",
    )
    coa.create_account(
        UUID(COMPANY), "3331100000", "VAT đầu ra", regime=R, actor=uuid4(), reason="c"
    )
    coa.create_account(
        UUID(COMPANY),
        "3331100001",
        "VAT KT nhóm A",
        parent_code="3331100000",
        regime=R,
        actor=uuid4(),
        reason="c",
    )
    from src.bricks.payment_terms.web_adapter import _series_service as ss

    for pfx in ("HD/", "PT/"):
        ss.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=uuid4(), reason="s")


def _inv_body(company_id):
    return {
        "company_id": company_id,
        "customer_name": "CTCP Khách hàng",
        "issue_date": "2026-08-20",
        "vat_rate": "0.1",
        "items": [
            {
                "account_code": "5111000001",
                "description": "Bán hàng hóa",
                "amount": "50000000",
            }
        ],
    }


class TestTT99EndToEnd:
    def test_invoice_post_journals_with_spec_codes(self, chief, seeded, tt99_company):
        r = chief.post("/api/v1/invoices", json=_inv_body(str(tt99_company.id)))
        assert r.status_code == 201, r.get_json()
        inv = r.get_json()["data"]
        assert inv["grand_total"] == 55_000_000.0

        p = chief.post(f"/api/v1/invoices/{inv['id']}/post", json={"reason": "ok"})
        assert p.status_code == 200, p.get_json()
        body = p.get_json()["data"]

        v = chief.get(f"/api/v1/vouchers/{body['voucher_id']}").get_json()["data"]
        assert v["status"] == "POSTED"
        assert v["total_debit"] == v["total_credit"] == 55_000_000.0

        tb = chief.get(
            "/api/v1/reports/trial-balance",
            query_string={
                "company_id": str(tt99_company.id),
                "from": "2026-08-01",
                "to": "2026-08-31",
            },
        ).get_json()["data"]
        codes = {row["account_code"] for row in tb}
        assert {"1311000001", "5111000001", "3331100001"} <= codes

    def test_short_code_rejected_for_tt99_company(self, chief, seeded, tt99_company):
        bad = _inv_body(str(tt99_company.id))
        bad["items"] = [dict(bad["items"][0], account_code="5111")]
        r = chief.post("/api/v1/invoices", json=bad)
        assert r.status_code == 422
