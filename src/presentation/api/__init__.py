"""API blueprint — Company endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import sessionmaker

from src.application.services.company_service import CompanyService
from src.domain.entities.base import AccountingRegime, CompanyType, CompanyStatus, TaxId
from src.domain.exceptions import (
    CompanyLockedError,
    CompanyNotFoundError,
    DuplicateMSTError,
    InvalidCompanyTypeError,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import Base
from src.infrastructure.repositories import SQLAlchemyCompanyRepository

api_bp = Blueprint("api", __name__)

logger = logging.getLogger(__name__)

# ── Test engine hook (set by tests before making requests) ─────────────────
_test_engine = None


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


def _req_session():
    """Get a session tied to the test engine when set, else fall back to app db."""
    if _test_engine is not None:
        return sessionmaker(bind=_test_engine)()
    return db.session


def _service() -> CompanyService:
    """Build CompanyService using the current request-bound session."""
    db.session = _req_session()  # type: ignore[assignment]
    try:
        repo = SQLAlchemyCompanyRepository()
        return CompanyService(company_repo=repo)
    finally:
        pass  # plain session auto-closed by test teardown


# Company type / status conversion from string (JSON) to enum (domain)
_COMPANY_TYPE_MAP = {e.value: e for e in CompanyType}
_ACCOUNTING_REGIME_MAP = {e.value: e for e in AccountingRegime}
_COMPANY_STATUS_MAP = {e.value: e for e in CompanyStatus}


def _convert_enums(data: dict) -> dict:
    """Convert string enum values from JSON to domain enum instances."""
    result = dict(data)  # shallow copy
    if "company_type" in result and isinstance(result["company_type"], str):
        result["company_type"] = _COMPANY_TYPE_MAP.get(result["company_type"])
    if "accounting_regime" in result and isinstance(result["accounting_regime"], str):
        result["accounting_regime"] = _ACCOUNTING_REGIME_MAP.get(result["accounting_regime"])
    if "status" in result and isinstance(result["status"], str):
        result["status"] = _COMPANY_STATUS_MAP.get(result["status"])
    # Convert date strings (ISO format) back to date objects
    for _key in ("business_reg_date", "created_at", "updated_at"):
        if _key in result and isinstance(result[_key], str):
            from datetime import date as _d
            try:
                result[_key] = _d.fromisoformat(result[_key])
            except ValueError:
                pass  # keep as string if cannot parse
    return _convert_bankaccounts(result)


def _convert_bankaccounts(data: dict) -> dict:
    """Convert bank_accounts list of dicts to list of BankAccount instances."""
    ba_list = data.get("bank_accounts")
    if isinstance(ba_list, list):
        converted = []
        for ba in ba_list:
            if isinstance(ba, dict):
                from src.domain.entities.company import BankAccount as BA
                converted.append(
                    BA(
                        bank_name=ba.get("bank_name", ""),
                        account_number=ba.get("account_number", ""),
                        account_holder=ba.get("account_holder", ""),
                        branch=ba.get("branch", ""),
                        is_primary=ba.get("is_primary", False),
                    )
                )
            else:
                converted.append(ba)
        data = dict(data)  # shallow copy
        data["bank_accounts"] = converted
    return data


# ── Health ──────────────────────────────────────────────────────────────────


@api_bp.get("/health")
def health():
    return {"status": "ok", "module": "api"}


# ── Company CRUD ─────────────────────────────────────────────────────────────


@api_bp.post("/v1/companies")
def create_company():
    """Create a new company record."""
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.pop("actor", "00000000-0000-0000-0000-000000000000"))
        data["mst"] = TaxId(data["mst"])

        data = _convert_enums(data)

        service = _service()
        company = service.create_company(actor=actor, **data)
        return jsonify(_serialize_company(company)), 201
    except DuplicateMSTError as exc:
        return jsonify({"error": str(exc), "code": "MST_TAKEN"}), 409
    except (ValueError, InvalidCompanyTypeError) as exc:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(exc), "code": "INVALID_INPUT"}), 422
    except Exception as exc:  # noqa: BLE001
        import traceback; traceback.print_exc()
        logger.exception("create_company failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/companies")
def list_companies():
    """List active companies."""
    try:
        service = _service()
        companies = service._company_repo.list_active()
        return jsonify(
            {
                "data": [_serialize_company(c) for c in companies],
                "pagination": {"page": 1, "page_size": 20},
            }
        )
    finally:
        pass  # sessions managed by test engine teardown


@api_bp.get("/v1/companies/<uuid:company_id>")
def get_company(company_id: UUID):
    """Retrieve a single company by id."""
    try:
        service = _service()
        company = service.get_company(company_id)
        return jsonify(_serialize_company(company))
    except CompanyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    finally:
        pass


@api_bp.patch("/v1/companies/<uuid:company_id>")
def update_company(company_id: UUID):
    """Partially update a company."""
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.pop("actor", "00000000-0000-0000-0000-000000000000"))
        service = _service()
        company = service.update_company(company_id, actor=actor, **data)
        return jsonify(_serialize_company(company))
    except CompanyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except CompanyLockedError as exc:
        return jsonify({"error": str(exc), "code": "COMPANY_LOCKED"}), 403
    finally:
        pass


# ── Lifecycle actions ────────────────────────────────────────────────────────


@api_bp.post("/v1/companies/<uuid:company_id>/suspend")
def suspend_company(company_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor", "00000000-0000-0000-0000-000000000000"))
        service = _service()
        company = service.deactivate_company(company_id, actor=actor)
        return jsonify(_serialize_company(company))
    except CompanyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except CompanyLockedError as exc:
        return jsonify({"error": str(exc), "code": "COMPANY_LOCKED"}), 403
    finally:
        pass


@api_bp.post("/v1/companies/<uuid:company_id>/reactivate")
def reactivate_company(company_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor", "00000000-0000-0000-0000-000000000000"))
        service = _service()
        from src.domain.entities.company import CompanyStatus

        company = service.update_company(
            company_id, actor=actor, status=CompanyStatus.ACTIVE
        )
        return jsonify(_serialize_company(company))
    except CompanyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except CompanyLockedError as exc:
        return jsonify({"error": str(exc), "code": "COMPANY_LOCKED"}), 403
    finally:
        pass


@api_bp.post("/v1/companies/<uuid:company_id>/dissolve")
def dissolve_company_endpoint(company_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor", "00000000-0000-0000-0000-000000000000"))
        service = _service()
        company = service.dissolve_company(company_id, actor=actor)
        return jsonify(_serialize_company(company))
    except CompanyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except CompanyLockedError as exc:
        return jsonify({"error": str(exc), "code": "COMPANY_LOCKED"}), 403
    finally:
        pass


# ── Serializer ──────────────────────────────────────────────────────────────


def _serialize_company(company) -> dict:
    """Minimal JSON representation — expands as API grows."""
    return {
        "id": str(company.id),
        "legal_name": company.legal_name,
        "mst": str(company.mst),
        "company_type": company.company_type.value,
        "accounting_regime": company.accounting_regime.value,
        "status": company.status.value,
        "is_active": company.is_active,
        "created_at": company.created_at.isoformat(),
        "updated_at": company.updated_at.isoformat(),
    }