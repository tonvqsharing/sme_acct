"""Read APIs for COA / fiscal-year / audit-log — auditor-accessible."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.app import create_app
from tests.integration.conftest import (
    UUID_AUDITOR,
    FakeUser,
    _store,
)

COMPANY = "66666666-6666-6666-6666-666666666666"


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
    app.coa_service.create_account(UUID(COMPANY), "111", "Tiền mặt", actor=_u(), reason="c")


class TestCoaReads:
    def test_list_and_detail(self, auditor, seeded):
        r = auditor.get("/api/v1/accounts", query_string={"company_id": COMPANY})
        assert r.status_code == 200
        assert r.get_json()["data"][0]["code"] == "111"
        d = auditor.get("/api/v1/accounts/111", query_string={"company_id": COMPANY})
        assert d.get_json()["data"]["is_detail"] is False

    def test_unknown_account_404(self, auditor, seeded):
        r = auditor.get("/api/v1/accounts/999", query_string={"company_id": COMPANY})
        assert r.status_code == 404


class TestFyReads:
    def test_years_and_periods(self, auditor, seeded):
        ys = auditor.get("/api/v1/fiscal-years", query_string={"company_id": COMPANY}).get_json()[
            "data"
        ]
        assert len(ys) == 1 and ys[0]["status"] == "OPEN"
        ps = auditor.get(f"/api/v1/fiscal-years/{ys[0]['id']}/periods").get_json()["data"]
        assert len(ps) == 12
        assert ps[0]["start_date"] == "2026-01-01"


class TestAuditLogReads:
    def test_events_queryable_with_chain_fields(self, auditor, app, seeded):
        # Generate an audit event via payment-terms creation (CREATE stamps)
        from uuid import uuid4 as _u

        from src.bricks.payment_terms.web_adapter import _term_service

        term = _term_service().create_payment_term(
            company_id=UUID(COMPANY),
            name="Net 7",
            due_days=7,
            interest_rate=0,
            actor=_u(),
            reason="audit-seed",
        )
        r = auditor.get(
            "/api/v1/audit-log",
            query_string={
                "entity_type": "payment_term",
                "entity_id": str(term.id),
            },
        )
        assert r.status_code == 200
        ev = r.get_json()["data"]
        assert ev and ev[0]["action"] == "CREATE"
        assert len(ev[0]["checksum"]) == 64

    def test_missing_params_422(self, auditor):
        assert auditor.get("/api/v1/audit-log").status_code == 422

    def test_unauthenticated_401(self, app, seeded):
        r = app.test_client().get(
            "/api/v1/audit-log",
            query_string={"entity_type": "payment_term", "entity_id": str(uuid4())},
        )
        assert r.status_code == 401
