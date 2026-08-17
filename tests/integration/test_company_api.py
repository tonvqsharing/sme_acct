"""Integration tests for Company REST API — Flask test client + shared in-memory SQLite."""

from __future__ import annotations

import dataclasses
import enum
import os
import sys
from datetime import date
from uuid import UUID, uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

import pytest
from flask import Flask

from src.domain.entities.base import AccountingRegime, CompanyType, TaxId
from src.domain.entities.company import BankAccount, Company, CompanyStatus
from src.domain.exceptions import DuplicateMSTError, NotFoundError
from src.infrastructure.database import db
from src.infrastructure.database.models import Base
from src.infrastructure.repositories import SQLAlchemyCompanyRepository
from src.presentation.api import api_bp, init_test_engine, clear_test_engine

ACTOR = UUID("22222222-2222-2222-2222-222222222222")


def _make_kwargs(**overrides):
    base = {
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": TaxId("0123456789"),
        "headquarters_address": "123 Nguyễn Văn Linh, P. Tân Phong, Q.7, TP.HCM",
        "legal_representative": "Nguyễn Văn A",
        "business_reg_number": "0312345678",
        "business_reg_date": date(2020, 1, 15),
        "business_fields": ["6202", "4791"],
        "company_type": CompanyType.MULTI_LLC,
        "accounting_regime": AccountingRegime.TT99,
        "fiscal_year_start_month": 1,
        "fiscal_year_start_day": 1,
        "responsible_accountant_name": "Trần Thị B",
        "responsible_accountant_license": "KHMN-01234",
        "tax_agency": "Chi cục Thuế Q.7",
        "controlling_tax_office": "Cục Thuế TP.HCM",
        "bhxh_code": "0070123456",
        "bhxh_agency": "BHXH Quận 7",
        "authorized_capital": 1_000_000_000,
        "phone": "0281234567",
        "email": "info@abc.com",
        "website": "https://abc.com",
        "short_name": "ABC Co.",
        "bank_accounts": [
            BankAccount("VCB", "0071234567890", "Cty ABC", "PGD Q.7", is_primary=True),
        ],
        "status": CompanyStatus.ACTIVE,
        "is_active": True,
        "created_by": ACTOR,
        "updated_by": ACTOR,
        "config_version": 1,
        "legal_reviewed_at": None,
        "legal_reviewed_by": None,
        "mst_changed_at": None,
        "created_at": date(2024, 1, 1),
        "updated_at": date(2024, 1, 1),
    }
    base.update(overrides)
    return base


def _json_payload(kwargs: dict) -> dict:
    """Recursively convert enums, UUIDs, dates, dataclass instances → JSON-serializable.

    TaxId and AccountCode are frozen value-object dataclasses but behave like
    strings — they serialize via str(value), not as dicts.
    BankAccount → reconstruct from dict so Company.__post_init__ gets real instances.
    """

    def convert(value):
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, date):
            return value.isoformat()
        # Value-object dataclasses: serialize as string via __str__
        if isinstance(value, (TaxId,)):
            return str(value)
        # Reconstruct BankAccount from dict so Company gets real instances
        if isinstance(value, dict):
            ba_fields = {"bank_name", "account_number", "account_holder", "branch", "is_primary"}
            if ba_fields.issubset(value.keys()):
                # Filter to only BankAccount fields + return as dict for JSON later
                # But we need to return BankAccount instance for the API→service path
                # So: convert to BankAccount instance
                from src.domain.entities.company import BankAccount as BA
                ba = BA(
                    bank_name=value.get("bank_name", ""),
                    account_number=value.get("account_number", ""),
                    account_holder=value.get("account_holder", ""),
                    branch=value.get("branch", ""),
                    is_primary=value.get("is_primary", False),
                )
                return ba
        # Only convert actual dataclass instances (not dataclass factory types)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return {
                k: convert(v)
                for k, v in dataclasses.asdict(value).items()
                if not k.startswith("_")
            }
        if isinstance(value, list):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        return value

    result = {}
    for key, val in kwargs.items():
        if key == "actor":
            result[key] = str(val) if isinstance(val, UUID) else val
            continue
        result[key] = convert(val)
    return result


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def app():
    """Fresh Flask app with in-memory SQLite, per test."""
    application = Flask(__name__)
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    application.config["SECRET_KEY"] = "test-secret"
    application.config["TESTING"] = True
    db.init_app(application)
    with application.app_context():
        engine = db.engine
        Base.metadata.create_all(engine)
        init_test_engine(engine)
        yield application
        clear_test_engine()


@pytest.fixture()
def client(app):
    """Test client with Company API pre-registered."""
    app.register_blueprint(api_bp, url_prefix="/api")
    return app.test_client()


@pytest.fixture()
def repo(app):
    """SQLAlchemyCompanyRepository bound to the shared in-memory DB."""
    with app.app_context():
        original = db.session
        plain = sessionmaker(bind=db.engine)()
        db.session = plain  # type: ignore[assignment]
        try:
            yield SQLAlchemyCompanyRepository()
        finally:
            db.session = original  # type: ignore[assignment]
            close_all_sessions()


# ── Tests ───────────────────────────────────────────────────────────────────


class TestHealth:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"


class TestCreateCompany:
    def test_create_returns_201_with_body(self, client):
        r = client.post("/api/v1/companies", json=_json_payload(_make_kwargs()))
        assert r.status_code == 201
        body = r.get_json()
        assert body["id"] is not None
        assert body["legal_name"] == "Công ty TNHH ABC Việt Nam"
        assert body["mst"] == "0123456789"
        assert body["status"] == "active"
        assert body["company_type"] == "multi_llc"

    def test_duplicate_mst_returns_409(self, client, repo):
        # Seed via repo directly (shared DB via init_test_engine)
        c = Company(**_make_kwargs())
        repo.create(c)

        r = client.post(
            "/api/v1/companies",
            json=_json_payload(_make_kwargs(mst=TaxId(str(c.mst)))),
        )
        assert r.status_code == 409
        assert r.get_json()["code"] == "MST_TAKEN"

    def test_invalid_mst_returns_422(self, client):
        r = client.post(
            "/api/v1/companies",
            json=_json_payload(_make_kwargs(mst="bad-mst")),
        )
        assert r.status_code == 422


class TestListCompanies:
    def test_empty_when_none_created(self, client):
        r = client.get("/api/v1/companies")
        assert r.status_code == 200
        assert r.get_json()["data"] == []

    def test_returns_created_companies(self, client):
        # Create two companies via the API with unique MSTs
        r1 = client.post(
            "/api/v1/companies",
            json=_json_payload(_make_kwargs(legal_name="Cty A", mst="0123456789")),
        )
        assert r1.status_code == 201, f"Create A failed: {r1.get_json()}"
        r2 = client.post(
            "/api/v1/companies",
            json=_json_payload(_make_kwargs(legal_name="Cty B", mst="9876543210")),
        )
        assert r2.status_code == 201, f"Create B failed: {r2.get_json()}"
        # List and verify both appear
        r = client.get("/api/v1/companies")
        assert r.status_code == 200
        names = [c["legal_name"] for c in r.get_json()["data"]]
        assert "Cty A" in names
        assert "Cty B" in names


class TestGetCompany:
    def test_get_existing(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        r = client.get(f"/api/v1/companies/{saved.id}")
        assert r.status_code == 200
        assert r.get_json()["id"] == str(saved.id)

    def test_get_missing_returns_404(self, client):
        fake = UUID("99999999-9999-9999-9999-999999999999")
        r = client.get(f"/api/v1/companies/{fake}")
        assert r.status_code == 404
        assert r.get_json()["code"] == "NOT_FOUND"


class TestUpdateCompany:
    def test_update_active_company(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        r = client.patch(
            f"/api/v1/companies/{saved.id}",
            json={"legal_name": "New Name", "actor": str(ACTOR)},
        )
        assert r.status_code == 200
        assert r.get_json()["legal_name"] == "New Name"

    def test_update_not_found_returns_404(self, client):
        fake = UUID("99999999-9999-9999-9999-9999-999999999999")
        r = client.patch(
            f"/api/v1/companies/{fake}",
            json={"legal_name": "X", "actor": str(ACTOR)},
        )
        assert r.status_code == 404

    def test_update_suspended_returns_403(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        repo.update(Company(**_make_kwargs(id=saved.id, status=CompanyStatus.SUSPENDED)))
        r = client.patch(
            f"/api/v1/companies/{saved.id}",
            json={"legal_name": "X", "actor": str(ACTOR)},
        )
        assert r.status_code == 403


class TestSuspendCompany:
    def test_suspend_active(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        r = client.post(
            f"/api/v1/companies/{saved.id}/suspend",
            json={"actor": str(ACTOR)},
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "suspended"
        assert r.get_json()["is_active"] is False

    def test_suspend_not_found_returns_404(self, client):
        fake = UUID("99999999-9999-9999-9999-9999-999999999999")
        r = client.post(f"/api/v1/companies/{fake}/suspend", json={"actor": str(ACTOR)})
        assert r.status_code == 404


class TestDissolveCompany:
    def test_dissolve_active(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        r = client.post(
            f"/api/v1/companies/{saved.id}/dissolve",
            json={"actor": str(ACTOR)},
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "dissolved"
        assert r.get_json()["is_active"] is False

    def test_dissolve_already_dissolved_returns_403(self, client, repo):
        saved = repo.create(Company(**_make_kwargs()))
        saved.dissolve()
        repo.update(saved)

        r = client.post(
            f"/api/v1/companies/{saved.id}/dissolve",
            json={"actor": str(ACTOR)},
        )
        assert r.status_code == 403