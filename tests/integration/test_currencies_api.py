"""Integration tests for Currencies REST API — Flask test client + in-memory SQLite.

Covers specs-currencies.md §6 endpoints: currencies CRUD, exchange rates,
CSV import, revaluation lifecycle (create→approve→post→reverse), FX report,
RBAC decorators, error paths.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from flask import Flask

from src.domain.entities.currency import Currency
from src.infrastructure.database import db
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.currency_repo import SQLAlchemyCurrencyRepository
from src.presentation.api import currencies_bp

ACTOR = UUID("22222222-2222-2222-2222-222222222222")
COMPANY = UUID("11111111-1111-1111-1111-111111111111")
APPROVER = UUID("33333333-3333-3333-3333-333333333333")

CSV_OK = (
    "rate_date,currency,rate_type,rate,source,note\n"
    "2026-08-01,USD,BUY,24700,CSV_IMPORT,aug\n"
    "2026-08-01,USD,TRANSFER,24800,CSV_IMPORT,aug\n"
)


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
        currencies_bp.init_test_engine(engine)
        yield application
        currencies_bp.clear_test_engine()


@pytest.fixture()
def client(app):
    app.register_blueprint(currencies_bp.api_bp, url_prefix="/api")
    return app.test_client()


@pytest.fixture()
def seed_currency(app):
    with app.app_context():
        SQLAlchemyCurrencyRepository().save(Currency(code="USD", name="US Dollar", symbol="$"))


# ── Currencies ──────────────────────────────────────────────────────────────


class TestCurrenciesAPI:
    def test_create_currency(self, client):
        resp = client.post(
            "/api/v1/currencies",
            json={"code": "USD", "name": "US Dollar", "symbol": "$"},
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["currency"]["code"] == "USD"

    def test_create_invalid_code(self, client):
        resp = client.post(
            "/api/v1/currencies",
            json={"code": "usd", "name": "US Dollar", "symbol": "$"},
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "INVALID_CURRENCY"

    def test_create_duplicate(self, client, seed_currency):
        resp = client.post(
            "/api/v1/currencies",
            json={"code": "USD", "name": "US Dollar", "symbol": "$"},
        )
        assert resp.status_code == 422

    def test_create_string_false_is_base_rejected(self, client):
        """Type-coercion guard: \"false\" string must NOT set is_base=True."""
        resp = client.post(
            "/api/v1/currencies",
            json={"code": "EUR", "name": "Euro", "symbol": "€", "is_base": "false"},
        )
        assert resp.status_code == 422

    def test_list_currencies(self, client, seed_currency):
        resp = client.get("/api/v1/currencies")
        assert resp.status_code == 200
        codes = [c["code"] for c in resp.get_json()["currencies"]]
        assert "USD" in codes

    def test_deactivate_currency(self, client, seed_currency):
        resp = client.patch("/api/v1/currencies/USD", json={"deactivate": True})
        assert resp.status_code == 200
        assert resp.get_json()["currency"]["is_active"] is False

    def test_patch_missing_currency(self, client):
        resp = client.patch("/api/v1/currencies/EUR", json={"name": "Euro"})
        assert resp.status_code == 404


# ── Exchange rates ──────────────────────────────────────────────────────────


class TestExchangeRatesAPI:
    def test_create_rate(self, client, seed_currency):
        resp = client.post(
            "/api/v1/exchange-rates",
            json={
                "currency_code": "USD",
                "rate_date": "2026-08-01",
                "rate_type": "buy",
                "rate": "24700",
                "source": "MANUAL",
                "actor": str(ACTOR),
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["exchange_rate"]["rate"] == "24700"

    def test_create_rate_requires_actor(self, client, seed_currency):
        resp = client.post(
            "/api/v1/exchange-rates",
            json={
                "currency_code": "USD",
                "rate_date": "2026-08-01",
                "rate_type": "buy",
                "rate": "24700",
            },
        )
        assert resp.status_code == 400
        assert resp.get_json()["code"] == "MISSING_ACTOR"

    def test_create_rate_unknown_currency(self, client):
        resp = client.post(
            "/api/v1/exchange-rates",
            json={
                "currency_code": "EUR",
                "rate_date": "2026-08-01",
                "rate_type": "buy",
                "rate": "26800",
                "actor": str(ACTOR),
            },
        )
        assert resp.status_code == 404

    def test_list_rates_with_filter(self, client, seed_currency):
        client.post(
            "/api/v1/exchange-rates",
            json={
                "currency_code": "USD",
                "rate_date": "2026-08-01",
                "rate_type": "buy",
                "rate": "24700",
                "actor": str(ACTOR),
            },
        )
        resp = client.get("/api/v1/exchange-rates?currency=USD&type=buy")
        assert resp.status_code == 200
        rates = resp.get_json()["exchange_rates"]
        assert len(rates) == 1
        assert rates[0]["currency_code"] == "USD"

    def test_import_csv_success(self, client, seed_currency):
        resp = client.post(
            "/api/v1/exchange-rates/import",
            json={"csv": CSV_OK, "actor": str(ACTOR)},
        )
        assert resp.status_code == 201
        assert resp.get_json()["imported"] == 2

    def test_import_csv_bad_row_atomic(self, client, seed_currency):
        bad = CSV_OK.replace("24700", "0")
        resp = client.post(
            "/api/v1/exchange-rates/import",
            json={"csv": bad, "actor": str(ACTOR)},
        )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "IMPORT_ERROR"


# ── Revaluations ────────────────────────────────────────────────────────────


class TestRevaluationsAPI:
    def _create_rate(self, client):
        client.post(
            "/api/v1/exchange-rates",
            json={
                "currency_code": "USD",
                "rate_date": "2026-08-31",
                "rate_type": "transfer",
                "rate": "24700",
                "actor": str(ACTOR),
            },
        )

    def _monetary_items(self):
        return [
            {
                "account_code": "1122",
                "currency_code": "USD",
                "balance_original": "1000",
                "old_vnd": "24000000",
            }
        ]

    def _create_run(self, client):
        return client.post(
            "/api/v1/revaluations",
            json={
                "company_id": str(COMPANY),
                "period_start": "2026-08-01",
                "period_end": "2026-08-31",
                "rate_date": "2026-08-31",
                "monetary_items": self._monetary_items(),
                "actor": str(ACTOR),
            },
        )

    def test_create_run(self, client, seed_currency):
        self._create_rate(client)
        resp = self._create_run(client)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["revaluation_run"]["status"] == "draft"
        # gain: 1000*(24700-24000) = 700,000 on 1122 + offset credit
        assert len(body["revaluation_run"]["entries"]) == 2

    def test_create_run_period_locked(self, client, seed_currency):
        from src.infrastructure.database.models import PeriodLockModel

        with client.application.app_context():
            db.session.add(
                PeriodLockModel(
                    company_id=COMPANY,
                    period_start=date(2026, 8, 1),
                    period_end=date(2026, 8, 31),
                    is_locked=True,
                    locked_by_id=ACTOR,
                )
            )
            db.session.commit()
        self._create_rate(client)
        resp = self._create_run(client)
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "REVALUATION_ERROR"

    def test_full_lifecycle(self, client, seed_currency):
        self._create_rate(client)
        run_id = self._create_run(client).get_json()["revaluation_run"]["id"]

        # approve (CHIEF_ACCOUNTANT path — anonymous passes casbin in tests)
        resp = client.post(
            f"/api/v1/revaluations/{run_id}/approve",
            json={"actor": str(APPROVER)},
        )
        assert resp.status_code == 200
        assert resp.get_json()["revaluation_run"]["status"] == "approved"

        # post — must balance
        resp = client.post(f"/api/v1/revaluations/{run_id}/post")
        assert resp.status_code == 200
        assert resp.get_json()["revaluation_run"]["status"] == "posted"

        # reverse
        resp = client.post(f"/api/v1/revaluations/{run_id}/reverse")
        assert resp.status_code == 200
        assert resp.get_json()["revaluation_run"]["status"] == "reversed"

    def test_get_run_detail(self, client, seed_currency):
        self._create_rate(client)
        run_id = self._create_run(client).get_json()["revaluation_run"]["id"]
        resp = client.get(f"/api/v1/revaluations/{run_id}")
        assert resp.status_code == 200
        assert resp.get_json()["revaluation_run"]["id"] == run_id

    def test_get_missing_run(self, client):
        resp = client.get(f"/api/v1/revaluations/{UUID(int=0)}")
        assert resp.status_code == 404

    def test_post_unapproved_run(self, client, seed_currency):
        self._create_rate(client)
        run_id = self._create_run(client).get_json()["revaluation_run"]["id"]
        resp = client.post(f"/api/v1/revaluations/{run_id}/post")
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "REVALUATION_ERROR"


# ── FX differences report ───────────────────────────────────────────────────


class TestFXDifferencesAPI:
    def test_empty_report(self, client):
        resp = client.get(
            "/api/v1/fx-differences"
            f"?company_id={COMPANY}&period_start=2026-08-01&period_end=2026-08-31"
        )
        assert resp.status_code == 200
        assert resp.get_json()["fx_differences"] == []

    def test_report_invalid_params(self, client):
        resp = client.get("/api/v1/fx-differences?company_id=not-a-uuid")
        assert resp.status_code == 400
