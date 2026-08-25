"""Reports API — journal + trial balance off posted vouchers, real factory."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from tests.integration.conftest import (
    UUID_AUDITOR,
    FakeUser,
    _store,
)

COMPANY = "44444444-4444-4444-4444-444444444444"


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
    coa.create_account(UUID(COMPANY), "112", "TG", actor=_u(), reason="c")
    coa.create_account(
        UUID(COMPANY),
        "1121",
        "TGNH",
        parent_code="112",
        actor=_u(),
        reason="c",
    )
    coa.create_account(UUID(COMPANY), "5111", "DT", actor=_u(), reason="c")
    from src.bricks.payment_terms.web_adapter import _series_service

    for pfx in ("PT/", "PC/"):
        _series_service.create_series(company_id=UUID(COMPANY), prefix=pfx, actor=_u(), reason="s")
    vs = app.voucher_service if hasattr(app, "voucher_service") else None
    from src.bricks.voucher.web_adapter import _voucher_service

    svc = vs or _voucher_service
    v1 = svc.create_voucher(
        company_id=UUID(COMPANY),
        entry_date=date(2026, 8, 1),
        description="thu",
        lines=[
            {"account_code": "1121", "debit": "1000000", "credit": "0"},
            {"account_code": "5111", "debit": "0", "credit": "1000000"},
        ],
        actor=uuid4(),
        reason="r",
    )
    svc.post_voucher(v1.id, actor=uuid4(), reason="post")
    v2 = svc.create_voucher(
        company_id=UUID(COMPANY),
        entry_date=date(2026, 9, 10),
        description="chi",
        lines=[
            {"account_code": "1121", "debit": "0", "credit": "300000"},
            {"account_code": "5111", "debit": "300000", "credit": "0"},
        ],
        actor=uuid4(),
        reason="r",
    )
    # v2 left DRAFT — must NOT appear in reports
    return {"draft_id": str(v2.id)}


QS = {
    "company_id": COMPANY,
    "from": "2026-08-01",
    "to": "2026-09-30",
}


class TestReports:
    def test_general_journal_posted_only_chronological(self, auditor, seeded):
        r = auditor.get("/api/v1/reports/general-journal", query_string=QS)
        assert r.status_code == 200
        entries = r.get_json()["data"]
        assert [e["number"] for e in entries] == ["PT/000001"]
        assert entries[0]["total_debit"] == 1000000.0

    def test_trial_balance_totals_and_net(self, auditor, seeded):
        r = auditor.get("/api/v1/reports/trial-balance", query_string=QS)
        assert r.status_code == 200
        body = r.get_json()
        rows = {x["account_code"]: x for x in body["data"]}
        assert rows["1121"]["net_debit"] == 1000000.0  # DRAFT Sep voucher excluded
        assert body["totals"]["debit"] == body["totals"]["credit"]

    def test_unauthenticated_401(self, app):
        r = app.test_client().get("/api/v1/reports/trial-balance", query_string=QS)
        assert r.status_code == 401

    def test_bad_params_422(self, auditor):
        r = auditor.get(
            "/api/v1/reports/trial-balance",
            query_string={"company_id": "nope", "from": "x", "to": "y"},
        )
        assert r.status_code == 422
