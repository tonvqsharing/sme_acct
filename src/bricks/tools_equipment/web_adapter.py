"""Web adapter — Tools & Equipment (CCDC) Flask blueprint + routes.

ONLY file allowed to import Flask.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from src.bricks.tools_equipment.domain import (
    CCDCCategory,
    ToolEquipmentStatus,
    ValidationError,
)
from src.bricks.tools_equipment.services import AllocationEngine, ToolEquipmentService

# ---------------------------------------------------------------------------
# RBAC helpers
# ---------------------------------------------------------------------------

ADMIN_ROLES = {"ADMIN"}
CREATE_ROLES = {"ADMIN", "ACCOUNTANT"}
MODIFY_ROLES = {"ADMIN", "ACCOUNTANT"}
CHIEF_ONLY_ROLES = {"CHIEF_ACCOUNTANT"}
ALLOCATE_ROLES = {"ADMIN", "ACCOUNTANT"}
ALL_ROLES = {"ADMIN", "ACCOUNTANT", "CHIEF_ACCOUNTANT", "AUDITOR"}


def _require_role(allowed: set[str]) -> None:
    """Check current_user.role is in allowed set."""
    if not hasattr(current_user, "role"):
        raise PermissionError("No role")
    if current_user.role not in allowed:
        raise PermissionError(f"Role {current_user.role!r} not in {allowed}")


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

bp = Blueprint(
    "tools_equipment",
    __name__,
    url_prefix="/api/v1/tools-equipment",
)


def _error(message: str, status: int = 400) -> tuple[Any, int]:
    """Standard error response."""
    return jsonify({"error": message}), status


# ---------------------------------------------------------------------------
# CCDC Master endpoints
# ---------------------------------------------------------------------------


@bp.route("", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
def create_ccdc() -> tuple[Any, int]:
    """Create a new CCDC record."""
    try:
        _require_role(CREATE_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    data = request.get_json()
    if not data:
        return _error("Request body required", 400)

    try:
        svc: ToolEquipmentService = _get_service()
        entity = svc.create(
            company_id=current_user.company_id,
            code=data["code"],
            name=data["name"],
            category=CCDCCategory(data["category"]),
            purchase_date=date.fromisoformat(data["purchase_date"]),
            purchase_price=Decimal(str(data["purchase_price"])),
            useful_life_months=int(data["useful_life_months"]),
            expense_account_code=data["expense_account_code"],
            actor_id=UUID(str(current_user.id)),
            salvage_value=Decimal(str(data.get("salvage_value", 0))),
            prepaid_account_code=data.get("prepaid_account_code"),
            assigned_to=(UUID(data["assigned_to"]) if data.get("assigned_to") else None),
            cost_center_id=(UUID(data["cost_center_id"]) if data.get("cost_center_id") else None),
            dimension_value_id=(
                UUID(data["dimension_value_id"]) if data.get("dimension_value_id") else None
            ),
            description=data.get("description"),
        )
        return jsonify({"data": _serialize_entity(entity)}), 201
    except ValidationError as e:
        return _error(str(e), 400)
    except KeyError as e:
        return _error(f"Missing required field: {e}", 400)
    except (ValueError, TypeError) as e:
        return _error(f"Invalid value: {e}", 400)


@bp.route("", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
def list_ccdc() -> tuple[Any, int]:
    """List CCDC for the current company."""
    try:
        _require_role(ALL_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    svc: ToolEquipmentService = _get_service()

    # Optional filters
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")

    status = None
    if status_filter:
        try:
            status = ToolEquipmentStatus(status_filter)
        except ValueError:
            return _error(f"Invalid status: {status_filter}", 400)

    category = None
    if category_filter:
        try:
            category = CCDCCategory(category_filter)
        except ValueError:
            return _error(f"Invalid category: {category_filter}", 400)

    items = svc.list_by_company(
        current_user.company_id,
        status=status,
        category=category,
    )
    return jsonify({"data": [_serialize_entity(i) for i in items]}), 200


@bp.route("/<uuid:ccdc_id>", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
def get_ccdc(ccdc_id: UUID) -> tuple[Any, int]:
    """Get CCDC detail by ID."""
    try:
        _require_role(ALL_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    svc: ToolEquipmentService = _get_service()
    entity = svc.get_by_id(ccdc_id, current_user.company_id)
    if entity is None:
        return _error("CCDC not found", 404)

    return jsonify({"data": _serialize_entity(entity)}), 200


@bp.route("/<uuid:ccdc_id>", methods=["PATCH"])
@login_required  # type: ignore[untyped-decorator]
def update_ccdc(ccdc_id: UUID) -> tuple[Any, int]:
    """Update a CCDC record."""
    try:
        _require_role(MODIFY_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    data = request.get_json()
    if not data:
        return _error("Request body required", 400)

    svc: ToolEquipmentService = _get_service()

    # Parse fields
    fields: dict[str, Any] = {}
    if "name" in data:
        fields["name"] = data["name"]
    if "category" in data:
        fields["category"] = CCDCCategory(data["category"])
    if "purchase_date" in data:
        fields["purchase_date"] = date.fromisoformat(data["purchase_date"])
    if "purchase_price" in data:
        fields["purchase_price"] = Decimal(str(data["purchase_price"]))
    if "useful_life_months" in data:
        fields["useful_life_months"] = int(data["useful_life_months"])
    if "salvage_value" in data:
        fields["salvage_value"] = Decimal(str(data["salvage_value"]))
    if "expense_account_code" in data:
        fields["expense_account_code"] = data["expense_account_code"]
    if "prepaid_account_code" in data:
        fields["prepaid_account_code"] = data["prepaid_account_code"]
    if "assigned_to" in data:
        fields["assigned_to"] = UUID(data["assigned_to"]) if data["assigned_to"] else None
    if "cost_center_id" in data:
        fields["cost_center_id"] = UUID(data["cost_center_id"]) if data["cost_center_id"] else None
    if "dimension_value_id" in data:
        fields["dimension_value_id"] = (
            UUID(data["dimension_value_id"]) if data["dimension_value_id"] else None
        )
    if "description" in data:
        fields["description"] = data["description"]

    try:
        entity = svc.update(ccdc_id, current_user.company_id, UUID(str(current_user.id)), **fields)
        return jsonify({"data": _serialize_entity(entity)}), 200
    except ValidationError as e:
        return _error(str(e), 400)
    except KeyError as e:
        return _error(f"Missing required field: {e}", 400)
    except (ValueError, TypeError) as e:
        return _error(f"Invalid value: {e}", 400)


@bp.route("/<uuid:ccdc_id>/deactivate", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
def deactivate_ccdc(ccdc_id: UUID) -> tuple[Any, int]:
    """Deactivate CCDC (ACTIVE → INACTIVE)."""
    try:
        _require_role(CHIEF_ONLY_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    svc: ToolEquipmentService = _get_service()
    try:
        entity = svc.deactivate(ccdc_id, current_user.company_id, UUID(str(current_user.id)))
        return jsonify({"data": _serialize_entity(entity)}), 200
    except ValidationError as e:
        return _error(str(e), 400)


@bp.route("/<uuid:ccdc_id>/reactivate", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
def reactivate_ccdc(ccdc_id: UUID) -> tuple[Any, int]:
    """Reactivate CCDC (INACTIVE → ACTIVE)."""
    try:
        _require_role(CHIEF_ONLY_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    svc: ToolEquipmentService = _get_service()
    try:
        entity = svc.reactivate(ccdc_id, current_user.company_id, UUID(str(current_user.id)))
        return jsonify({"data": _serialize_entity(entity)}), 200
    except ValidationError as e:
        return _error(str(e), 400)


@bp.route("/<uuid:ccdc_id>/write-off", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
def write_off_ccdc(ccdc_id: UUID) -> tuple[Any, int]:
    """Write off CCDC (requires CHIEF_ACCOUNTANT)."""
    try:
        _require_role(CHIEF_ONLY_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    svc: ToolEquipmentService = _get_service()
    try:
        entity = svc.write_off(ccdc_id, current_user.company_id, UUID(str(current_user.id)))
        return jsonify({"data": _serialize_entity(entity)}), 200
    except ValidationError as e:
        return _error(str(e), 400)


# ---------------------------------------------------------------------------
# Allocation endpoints
# ---------------------------------------------------------------------------


@bp.route("/allocate", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
def run_allocation() -> tuple[Any, int]:
    """Run monthly CCDC allocation."""
    try:
        _require_role(ALLOCATE_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    data = request.get_json()
    if not data:
        return _error("Request body required", 400)

    try:
        year = int(data["year"])
        month = int(data["month"])
    except (KeyError, ValueError):
        return _error("year and month are required integers", 400)

    engine: AllocationEngine = _get_allocation_engine()
    try:
        allocations = engine.post_allocations(current_user.company_id, year, month)
        return (
            jsonify(
                {
                    "data": {
                        "period_year": year,
                        "period_month": month,
                        "allocations": [_serialize_allocation(a) for a in allocations],
                        "total_count": len(allocations),
                    }
                }
            ),
            200,
        )
    except ValidationError as e:
        return _error(str(e), 400)


@bp.route("/<uuid:ccdc_id>/allocations", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
def list_allocations(ccdc_id: UUID) -> tuple[Any, int]:
    """List allocations for a CCDC item."""
    try:
        _require_role(ALL_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    # Verify CCDC exists and belongs to this company (security scoping)
    svc: ToolEquipmentService = _get_service()
    entity = svc.get_by_id(ccdc_id, current_user.company_id)
    if entity is None:
        return _error("CCDC not found", 404)

    year_filter = request.args.get("year")
    year = int(year_filter) if year_filter else None

    engine: AllocationEngine = _get_allocation_engine()
    allocations = engine.list_allocations(ccdc_id, year=year)
    return (
        jsonify(
            {
                "data": [_serialize_allocation(a) for a in allocations],
                "total_count": len(allocations),
            }
        ),
        200,
    )


# ---------------------------------------------------------------------------
# Report endpoints
# ---------------------------------------------------------------------------


@bp.route("/ledger", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
def get_ledger() -> tuple[Any, int]:
    """Get CCDC ledger (Sổ theo dõi CCDC)."""
    try:
        _require_role(ALL_ROLES)
    except PermissionError as e:
        return _error(str(e), 403)

    engine: AllocationEngine = _get_allocation_engine()
    year = int(request.args.get("year", datetime.now(UTC).date().year))

    summary = engine.get_allocation_summary(current_user.company_id, year)
    return jsonify({"data": summary}), 200


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_entity(entity: Any) -> dict[str, Any]:
    """Serialize ToolEquipment to JSON-friendly dict."""
    return {
        "id": str(entity.id),
        "company_id": str(entity.company_id),
        "code": entity.code,
        "name": entity.name,
        "category": entity.category.value,
        "purchase_date": entity.purchase_date.isoformat(),
        "purchase_price": str(entity.purchase_price),
        "useful_life_months": entity.useful_life_months,
        "salvage_value": str(entity.salvage_value),
        "monthly_allocation": str(entity.monthly_allocation),
        "remaining_value": str(entity.remaining_value),
        "expense_account_code": entity.expense_account_code,
        "prepaid_account_code": entity.prepaid_account_code,
        "assigned_to": str(entity.assigned_to) if entity.assigned_to else None,
        "cost_center_id": (str(entity.cost_center_id) if entity.cost_center_id else None),
        "dimension_value_id": (
            str(entity.dimension_value_id) if entity.dimension_value_id else None
        ),
        "description": entity.description,
        "status": entity.status.value,
        "audit_checksum": entity.audit_checksum,
        "created_by": str(entity.created_by) if entity.created_by else None,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }


def _serialize_allocation(entity: Any) -> dict[str, Any]:
    """Serialize ToolEquipmentAllocation to JSON-friendly dict."""
    return {
        "id": str(entity.id),
        "tool_equipment_id": str(entity.tool_equipment_id),
        "period_year": entity.period_year,
        "period_month": entity.period_month,
        "allocated_amount": str(entity.allocated_amount),
        "expense_account_code": entity.expense_account_code,
        "cost_center_id": (str(entity.cost_center_id) if entity.cost_center_id else None),
        "dimension_value_id": (
            str(entity.dimension_value_id) if entity.dimension_value_id else None
        ),
        "voucher_id": str(entity.voucher_id) if entity.voucher_id else None,
        "status": entity.status.value,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
    }


# ---------------------------------------------------------------------------
# Service getters (will be replaced by dependency injection in app.py)
# ---------------------------------------------------------------------------

_service: ToolEquipmentService | None = None
_allocation_engine: AllocationEngine | None = None


def _get_service() -> ToolEquipmentService:
    """Get the ToolEquipmentService instance."""
    if _service is None:
        raise RuntimeError("ToolEquipmentService not initialized")
    return _service


def _get_allocation_engine() -> AllocationEngine:
    """Get the AllocationEngine instance."""
    if _allocation_engine is None:
        raise RuntimeError("AllocationEngine not initialized")
    return _allocation_engine


def init_tools_equipment_bp(
    service: ToolEquipmentService,
    allocation_engine: AllocationEngine,
) -> None:
    """Initialize the blueprint with services (called from app.py)."""
    global _service, _allocation_engine
    _service = service
    _allocation_engine = allocation_engine
