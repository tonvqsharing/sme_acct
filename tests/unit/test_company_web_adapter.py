"""Tests for Company web adapter — Flask blueprint + REST endpoints.

TDD: RED phase — write tests before implementation.
Tests use Flask test client with in-memory SQLite.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from src.bricks.company.domain import (
    AccountingRegime,
    CompanyType,
)
from src.bricks.company.services import CompanyService, TenantService
from src.bricks.company.storage import Base, SQLAlchemyCompanyRepository
from src.bricks.company.web_adapter import init_company_services, web_adapter_bp

# ─── Fake user for Flask-Login ─────────────────────────────────────────────

_store: dict = {}


class FakeUser(UserMixin):
    def __init__(self, user_id, role="ADMIN"):
        self.id = user_id
        self.role = role


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture()
def app():
    """Create Flask app with in-memory SQLite + wired services."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    repo = SQLAlchemyCompanyRepository(session)
    company_svc = CompanyService(repo)
    tenant_svc = TenantService(company_svc)

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return _store.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        return "", 401

    # Wire services into blueprint
    init_company_services(company_svc, tenant_svc)

    app.register_blueprint(web_adapter_bp)
    return app


@pytest.fixture()
def client(app):
    """Flask test client with logged-in ADMIN user."""
    user = FakeUser("00000000-0000-0000-0000-000000000001", "ADMIN")
    _store[user.id] = user

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["_user_id"] = user.id
        yield c


@pytest.fixture()
def chief_client(app):
    """Flask test client with logged-in CHIEF_ACCOUNTANT user."""
    user = FakeUser("00000000-0000-0000-0000-000000000002", "CHIEF_ACCOUNTANT")
    _store[user.id] = user

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["_user_id"] = user.id
        yield c


# ─── POST /api/v1/companies ────────────────────────────────────────────────


class TestCreateCompany:
    def test_create_company_success(self, client):
        resp = client.post(
            "/api/v1/companies",
            json={
                "legal_name": "Công ty TNHH ABC",
                "mst": "0123456789",
                "company_type": "multi_llc",
                "accounting_regime": "tt99",
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["legal_name"] == "Công ty TNHH ABC"
        assert data["data"]["mst"] == "0123456789"
        assert data["data"]["status"] == "active"

    def test_create_company_duplicate_mst_returns_409(self, client):
        client.post(
            "/api/v1/companies",
            json={"legal_name": "C1", "mst": "0123456789"},
        )
        resp = client.post(
            "/api/v1/companies",
            json={"legal_name": "C2", "mst": "0123456789"},
        )
        assert resp.status_code == 409

    def test_create_company_missing_mst_returns_422(self, client):
        resp = client.post(
            "/api/v1/companies",
            json={"legal_name": "No MST"},
        )
        assert resp.status_code == 422

    def test_create_company_invalid_mst_returns_422(self, client):
        resp = client.post(
            "/api/v1/companies",
            json={"legal_name": "Bad", "mst": "abc"},
        )
        assert resp.status_code == 422


# ─── GET /api/v1/companies ─────────────────────────────────────────────────


class TestListCompanies:
    def test_list_companies_empty(self, client):
        resp = client.get("/api/v1/companies")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []

    def test_list_companies_returns_created(self, client):
        client.post(
            "/api/v1/companies",
            json={"legal_name": "Listed", "mst": "0123456789"},
        )
        resp = client.get("/api/v1/companies")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["legal_name"] == "Listed"


# ─── GET /api/v1/companies/{id} ────────────────────────────────────────────


class TestGetCompany:
    def test_get_company_success(self, client):
        create_resp = client.post(
            "/api/v1/companies",
            json={"legal_name": "Detail", "mst": "0123456789"},
        )
        company_id = create_resp.get_json()["data"]["id"]
        resp = client.get(f"/api/v1/companies/{company_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["legal_name"] == "Detail"

    def test_get_company_not_found(self, client):
        resp = client.get(f"/api/v1/companies/{uuid4()}")
        assert resp.status_code == 404


# ─── PATCH /api/v1/companies/{id} ──────────────────────────────────────────


class TestUpdateCompany:
    def test_update_company_success(self, client):
        create_resp = client.post(
            "/api/v1/companies",
            json={"legal_name": "Original", "mst": "0123456789"},
        )
        company_id = create_resp.get_json()["data"]["id"]
        resp = client.patch(
            f"/api/v1/companies/{company_id}",
            json={"legal_name": "Updated"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["legal_name"] == "Updated"

    def test_update_company_not_found(self, client):
        resp = client.patch(
            f"/api/v1/companies/{uuid4()}",
            json={"legal_name": "X"},
        )
        assert resp.status_code == 404


# ─── POST /api/v1/companies/{id}/suspend ────────────────────────────────────


class TestSuspendCompany:
    def test_suspend_company_success(self, chief_client):
        # Create via chief_client (CHIEF_ACCOUNTANT can also create if ADMIN check is bypassed in test)
        # Actually, suspend route only needs company to exist. Create with chief_client using ADMIN role override.
        # Simpler: use service directly to create, then test suspend via HTTP.
        from src.bricks.company.web_adapter import _company_service

        company = _company_service.create(
            legal_name="Suspend Me",
            mst="0123456789",
            company_type=CompanyType.MULTI_LLC,
            accounting_regime=AccountingRegime.TT99,
        )
        resp = chief_client.post(f"/api/v1/companies/{company.id}/suspend")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["status"] == "suspended"

    def test_suspend_company_not_found(self, chief_client):
        resp = chief_client.post(f"/api/v1/companies/{uuid4()}/suspend")
        assert resp.status_code == 404

    def test_suspend_company_wrong_role(self, client):
        """ADMIN cannot suspend — only CHIEF_ACCOUNTANT."""
        from src.bricks.company.web_adapter import _company_service

        company = _company_service.create(
            legal_name="No Suspend",
            mst="0123456789",
            company_type=CompanyType.MULTI_LLC,
            accounting_regime=AccountingRegime.TT99,
        )
        resp = client.post(f"/api/v1/companies/{company.id}/suspend")
        assert resp.status_code == 403
