"""Integration tests for Fiscal Year REST API — Flask test client + SQLite.

Covers test-plan A-01..A-09: list, create (quarter-aligned), detail, ensure,
close year, lock/unlock period, lock-status, history, validation errors.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from flask import Flask

from src.infrastructure.database import db
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.fiscal_year_repo import (
    SQLAlchemyFiscalYearRepository,
    SQLAlchemyPeriodLockRepository,
)
from src.presentation.api import fiscal_year_bp

ACTOR = UUID("22222222-2222-2222-2222-222222222222")
OTHER = UUID("33333333-3333-3333-3333-333333333333")
COMPANY = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture()
def app():
    application = Flask(__name__)
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    application.config["SECRET_KEY"] = "test-secret"
    application.config["TESTING"] = True
    db.init_app(application)
    with application.app_context():
        engine = db.engine
        Base.metadata.create_all(engine)
        fiscal_year_bp.init_test_engine(engine)
        yield application
        fiscal_year_bp.clear_test_engine()


@pytest.fixture()
def client(app):
    app.register_blueprint(fiscal_year_bp.api_bp, url_prefix="/api")
    return app.test_client()


@pytest.fixture()
def seeded_year(app):
    """Calendar FY 2026 pre-created in DB."""
    with app.app_context():
        from src.domain.entities.base import AccountingPeriodType
        from src.domain.entities.fiscal_year import FiscalYear

        fy = FiscalYear(
            company_id=COMPANY,
            period_type=AccountingPeriodType.CALENDAR,
            start_date=date(2026, 1, 1),
        )
        SQLAlchemyFiscalYearRepository().save(fy)
        return fy


def _lock_all_periods(app, fy):
    with app.app_context():
        lock_repo = SQLAlchemyPeriodLockRepository()
        for p in fy.periods:
            lock_repo.lock(p.id, actor=ACTOR, reason="khóa kỳ")


class TestFiscalYearsAPI:
    def test_a01_list_empty(self, client):
        resp = client.get(f"/api/v1/fiscal-years?company_id={COMPANY}")
        assert resp.status_code == 200
        assert resp.get_json()["fiscal_years"] == []

    def test_a02_list_requires_company(self, client):
        resp = client.get("/api/v1/fiscal-years")
        assert resp.status_code == 400

    def test_a03_create_quarter_aligned(self, client):
        resp = client.post(
            "/api/v1/fiscal-years",
            json={
                "company_id": str(COMPANY),
                "period_type": "fiscal_apr",
                "start_date": "2026-04-01",
                "actor": str(ACTOR),
            },
        )
        assert resp.status_code == 201
        body = resp.get_json()["fiscal_year"]
        assert body["year_code"] == "2026"
        assert body["start_date"] == "2026-04-01"
        assert body["end_date"] == "2027-03-31"
        assert len(body["periods"]) == 12
        assert body["periods"][0]["label"] == "Tháng 04/2026"

    def test_a04_create_non_quarter_rejected(self, client):
        resp = client.post(
            "/api/v1/fiscal-years",
            json={
                "company_id": str(COMPANY),
                "period_type": "calendar",
                "start_date": "2026-02-01",
                "actor": str(ACTOR),
            },
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "FISCAL_YEAR_ERROR"

    def test_a05_create_missing_actor(self, client):
        resp = client.post(
            "/api/v1/fiscal-years",
            json={
                "company_id": str(COMPANY),
                "period_type": "calendar",
                "start_date": "2026-01-01",
            },
        )
        assert resp.status_code == 400
        assert resp.get_json()["code"] == "MISSING_ACTOR"

    def test_a06_get_detail(self, client, seeded_year):
        resp = client.get(f"/api/v1/fiscal-years/{seeded_year.id}")
        assert resp.status_code == 200
        body = resp.get_json()["fiscal_year"]
        assert body["period_type"] == "calendar"
        assert len(body["periods"]) == 12

    def test_a07_get_missing_404(self, client):
        resp = client.get(f"/api/v1/fiscal-years/{UUID('99999999-9999-9999-9999-999999999999')}")
        assert resp.status_code == 404

    def test_a08_ensure_creates_and_idempotent(self, client, seeded_year):
        resp = client.post(
            "/api/v1/fiscal-years/ensure",
            json={"company_id": str(COMPANY), "entry_date": "2026-06-15"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["fiscal_year"]["year_code"] == "2026"

        # ensure for a different year seeds a new FY
        resp2 = client.post(
            "/api/v1/fiscal-years/ensure",
            json={"company_id": str(COMPANY), "entry_date": "2027-03-01"},
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["fiscal_year"]["year_code"] == "2027"

    def test_a09_close_year(self, client, app, seeded_year):
        _lock_all_periods(app, seeded_year)
        resp = client.post(
            f"/api/v1/fiscal-years/{seeded_year.id}/close",
            json={"company_id": str(COMPANY), "actor": str(ACTOR)},
        )
        assert resp.status_code == 200
        body = resp.get_json()["fiscal_year"]
        assert body["status"] == "YEAR_CLOSED"
        assert body["opening_balance_posted"] is True
        assert all(p["status"] == "YEAR_CLOSED" for p in body["periods"])

    def test_close_year_requires_all_locked(self, client, seeded_year):
        resp = client.post(
            f"/api/v1/fiscal-years/{seeded_year.id}/close",
            json={"company_id": str(COMPANY), "actor": str(ACTOR)},
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "FISCAL_YEAR_ERROR"


class TestPeriodsAPI:
    def test_lock_status_open(self, client, seeded_year):
        resp = client.get(f"/api/v1/periods/lock-status?company_id={COMPANY}&date=2026-02-10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["locked"] is False
        assert body["period"]["label"] == "Tháng 02/2026"

    def test_lock_then_status_locked(self, client, app, seeded_year):
        p2 = seeded_year.period_for_date(date(2026, 2, 10))
        resp = client.post(
            f"/api/v1/periods/{p2.id}/lock",
            json={"actor": str(ACTOR), "reason": "khóa tháng 02"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["event"]["action"] == "CLOSE"

        resp = client.get(f"/api/v1/periods/lock-status?company_id={COMPANY}&date=2026-02-10")
        assert resp.get_json()["locked"] is True

    def test_lock_period_in_closed_year_rejected(self, client, app, seeded_year):
        """Locking any period of a YEAR_CLOSED fiscal year must be refused —
        it would silently downgrade the closed year (bypasses reopen SOD/approval)."""
        _lock_all_periods(app, seeded_year)
        resp = client.post(
            f"/api/v1/fiscal-years/{seeded_year.id}/close",
            json={"company_id": str(COMPANY), "actor": str(ACTOR)},
        )
        assert resp.status_code == 200

        p1 = seeded_year.period_for_date(date(2026, 1, 10))
        resp = client.post(
            f"/api/v1/periods/{p1.id}/lock",
            json={"actor": str(OTHER), "reason": "khóa lại"},
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "FISCAL_YEAR_ERROR"

    def test_double_lock_rejected(self, client, app, seeded_year):
        p2 = seeded_year.period_for_date(date(2026, 2, 10))
        resp = client.post(
            f"/api/v1/periods/{p2.id}/lock",
            json={"actor": str(ACTOR), "reason": "khóa tháng 02"},
        )
        assert resp.status_code == 201
        resp = client.post(
            f"/api/v1/periods/{p2.id}/lock",
            json={"actor": str(OTHER), "reason": "khóa lần hai"},
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "FISCAL_YEAR_ERROR"

    def test_unlock_requires_other_actor(self, client, app, seeded_year):
        p2 = seeded_year.period_for_date(date(2026, 2, 10))
        with app.app_context():
            SQLAlchemyPeriodLockRepository().lock(p2.id, actor=ACTOR, reason="khóa")

        resp = client.post(
            f"/api/v1/periods/{p2.id}/unlock",
            json={"actor": str(ACTOR), "reason": "mở lại"},
        )
        assert resp.status_code == 422  # self-approval blocked (SOD)

        resp = client.post(
            f"/api/v1/periods/{p2.id}/unlock",
            json={"actor": str(OTHER), "reason": "điều chỉnh"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["event"]["action"] == "REOPEN"

    def test_unlock_missing_reason(self, client, app, seeded_year):
        p2 = seeded_year.period_for_date(date(2026, 2, 10))
        with app.app_context():
            SQLAlchemyPeriodLockRepository().lock(p2.id, actor=ACTOR, reason="khóa")
        resp = client.post(
            f"/api/v1/periods/{p2.id}/unlock",
            json={"actor": str(OTHER), "reason": " "},
        )
        assert resp.status_code == 422

    def test_history_chain(self, client, app, seeded_year):
        p2 = seeded_year.period_for_date(date(2026, 2, 10))
        with app.app_context():
            lock_repo = SQLAlchemyPeriodLockRepository()
            lock_repo.lock(p2.id, actor=ACTOR, reason="khóa")
            lock_repo.reopen(p2.id, actor=OTHER, reason="điều chỉnh")

        resp = client.get(f"/api/v1/periods/{p2.id}/history")
        assert resp.status_code == 200
        events = resp.get_json()["events"]
        assert [e["action"] for e in events] == ["CLOSE", "REOPEN"]
        assert events[1]["prev_checksum"] == events[0]["checksum"]

    def test_lock_missing_period_404(self, client):
        resp = client.post(
            f"/api/v1/periods/{UUID('99999999-9999-9999-9999-999999999999')}/lock",
            json={"actor": str(ACTOR), "reason": "x"},
        )
        assert resp.status_code == 404
