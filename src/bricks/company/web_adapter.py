"""Company web adapter — Flask blueprint + REST endpoints.

Layer 4: Presentation (Flask routes).
This is the ONLY file in the brick that imports Flask.
Uses services.py for business logic, contract.py for persistence.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.company.domain import (
    AccountingRegime,
    Company,
    CompanyType,
    DuplicateMSTError,
    TaxId,
)
from src.bricks.company.services import CompanyService, TenantService

logger = logging.getLogger(__name__)

web_adapter_bp = Blueprint("company", __name__)

# ─── Service instances (initialized by app factory) ────────────────────────

_company_service: CompanyService | None = None
_tenant_service: TenantService | None = None


def init_company_services(company_service: CompanyService, tenant_service: TenantService) -> None:
    """Wire services into the blueprint. Called by app factory."""
    global _company_service, _tenant_service
    _company_service = company_service
    _tenant_service = tenant_service


def _get_service() -> CompanyService | None:
    if _company_service is None:
        abort(500, description="CompanyService not initialized")
    return _company_service


def _get_tenant_service() -> TenantService | None:
    if _tenant_service is None:
        abort(500, description="TenantService not initialized")
    return _tenant_service


# ─── Helpers ───────────────────────────────────────────────────────────────


def _company_to_dict(company: Company) -> dict[str, Any]:
    """Serialize Company entity to JSON-safe dict."""
    return {
        "id": str(company.id),
        "legal_name": company.legal_name,
        "mst": company.mst.value,
        "headquarters_address": company.headquarters_address,
        "legal_representative": company.legal_representative,
        "company_type": company.company_type.value,
        "accounting_regime": company.accounting_regime.value,
        "status": company.status.value,
        "is_active": company.is_active,
        "fiscal_year_start_month": company.fiscal_year_start_month,
        "fiscal_year_start_day": company.fiscal_year_start_day,
        "authorized_capital": float(company.authorized_capital),
        "phone": company.phone,
        "email": company.email,
        "website": company.website,
        "short_name": company.short_name,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "config_version": company.config_version,
    }


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        abort(422, description="Invalid UUID format")
    raise RuntimeError("unreachable")


# ─── Routes ────────────────────────────────────────────────────────────────


# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@web_adapter_bp.post("/api/v1/companies")  # type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@login_required
def create_company() -> tuple[Any, int]:
    """Create new company. ADMIN role required."""
    if current_user.role != "ADMIN":
        abort(403, description="RBAC denied: ADMIN role required")

    data = request.get_json(silent=True)
    if not data:
        abort(422, description="Request body required")

    # Validate required fields
    mst = data.get("mst", "").strip()
    legal_name = data.get("legal_name", "").strip()
    if not mst or not legal_name:
        abort(422, description="legal_name and mst are required")

    # Validate MST format
    try:
        TaxId(mst)
    except ValueError:
        abort(422, description="MST format invalid")

    # Parse optional enum fields
    company_type = CompanyType.MULTI_LLC
    if "company_type" in data:
        try:
            company_type = CompanyType(data["company_type"])
        except ValueError:
            abort(422, description="Invalid company_type")

    accounting_regime = AccountingRegime.TT99
    if "accounting_regime" in data:
        try:
            accounting_regime = AccountingRegime(data["accounting_regime"])
        except ValueError:
            abort(422, description="Invalid accounting_regime")

    # Parse optional Decimal (validated but not passed to create — set via update)
    if "authorized_capital" in data:
        try:
            Decimal(str(data["authorized_capital"]))
        except (InvalidOperation, ValueError):
            abort(422, description="Invalid authorized_capital")

    try:
        svc = _get_service()
        assert svc is not None
        company = svc.create(
            legal_name=legal_name,
            mst=mst,
            company_type=company_type,
            accounting_regime=accounting_regime,
            created_by=UUID(current_user.id),
        )
    except DuplicateMSTError:
        abort(409, description="MST already registered")

    logger.info("Company created", extra={"company_id": str(company.id), "mst": mst})
    return jsonify({"data": _company_to_dict(company)}), 201


# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@web_adapter_bp.get("/api/v1/companies")  # type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@login_required
def list_companies() -> tuple[Any, int]:
    """List active companies."""
    svc = _get_service()
    assert svc is not None
    companies = svc.list_active()
    return jsonify({"data": [_company_to_dict(c) for c in companies]}), 200


# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@web_adapter_bp.get("/api/v1/companies/<company_id>")  # type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@login_required
def get_company(company_id: str) -> tuple[Any, int]:
    """Get company detail by ID."""
    cid = _parse_uuid(company_id)
    svc = _get_service()
    assert svc is not None
# type: ignore[union-attr]
    company = svc.get_by_id(cid)
    if company is None:
        abort(404, description="Company not found")
    return jsonify({"data": _company_to_dict(company)}), 200


# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@web_adapter_bp.patch("/api/v1/companies/<company_id>")  # type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@login_required
def update_company(company_id: str) -> tuple[Any, int]:
    """Update company. ADMIN or ACCOUNTANT role required."""
    if current_user.role not in ("ADMIN", "ACCOUNTANT"):
        abort(403, description="RBAC denied: ADMIN or ACCOUNTANT role required")

    cid = _parse_uuid(company_id)
    svc = _get_service()
    assert svc is not None
# type: ignore[union-attr]
    company = svc.get_by_id(cid)
    if company is None:
        abort(404, description="Company not found")

    data = request.get_json(silent=True)
    if not data:
        abort(422, description="Request body required")

    # Apply partial updates (restricted fields)
    if "legal_name" in data:
        company.legal_name = data["legal_name"]
    if "headquarters_address" in data:
        company.headquarters_address = data["headquarters_address"]
    if "legal_representative" in data:
        company.legal_representative = data["legal_representative"]
    if "phone" in data:
        company.phone = data["phone"]
    if "email" in data:
        company.email = data["email"]
    if "website" in data:
        company.website = data["website"]
    if "short_name" in data:
        company.short_name = data["short_name"]

    updated = svc.update(company, actor=UUID(current_user.id))
    logger.info("Company updated", extra={"company_id": str(updated.id)})
    return jsonify({"data": _company_to_dict(updated)}), 200


# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@web_adapter_bp.post("/api/v1/companies/<company_id>/suspend")  # type: ignore[untyped-decorator]
# type: ignore[untyped-decorator]
@login_required
def suspend_company(company_id: str) -> tuple[Any, int]:
    """Suspend company. CHIEF_ACCOUNTANT role required."""
    if current_user.role != "CHIEF_ACCOUNTANT":
        abort(403, description="RBAC denied: CHIEF_ACCOUNTANT role required")

    cid = _parse_uuid(company_id)
    svc = _get_service()
    assert svc is not None
# type: ignore[union-attr]
    company = svc.get_by_id(cid)
    if company is None:
        abort(404, description="Company not found")

# type: ignore[union-attr]
    deactivated = svc.deactivate(cid, actor=UUID(current_user.id))
    logger.info("Company suspended", extra={"company_id": str(cid)})
    return jsonify({"data": _company_to_dict(deactivated)}), 200
