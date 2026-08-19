"""API blueprint — Cost Centers & Dimensions endpoints.

REST-ish endpoints per coding convention. Follows currencies_bp.py pattern.
Actor UUID required on mutations (D11). @casbin_required enforcement.
AUDITOR read-only; no write operations for AUDITOR role.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request

from src.application.services.cost_center_service import (
    CoaCostCenterService,
    CoaDimensionService,
    CoaDimensionValueService,
)
from src.application.ports import (
    CostCenterRepositoryPort,
    DimensionRepositoryPort,
    DimensionValueRepositoryPort,
)
from src.domain.entities.cost_center import CostCenterStatus, DimensionValueStatus
from src.domain.exceptions import (
    DomainException,
    DuplicateMSTError,
    SystemAccountModificationError,
)
from src.infrastructure.database import db
from src.infrastructure.repositories.cost_center_repo import (
    SQLAlchemyCostCenterRepository,
    SQLAlchemyDimensionRepository,
    SQLAlchemyDimensionValueRepository,
)
from src.presentation.rbac import casbin_required
from src.presentation.serializers import (
    serialize_cost_center,
    serialize_dimension,
    serialize_dimension_value,
)
from src.presentation.rbac import READ_ROLES, LOCK_WRITE_ROLES, FY_ADMIN_ROLES

cost_center_bp = Blueprint("cost_center", __name__)
logger = logging.getLogger(__name__)

READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")  # no AUDITOR
FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # no AUDITOR

# Service per-request factory (currencies pattern)
_service_cc = None
_service_dim = None
_service_dv = None


def _service_cc() -> CoaCostCenterService:
    global _service_cc
    if _service_cc is None:
        repo = SQLAlchemyCostCenterRepository()
        _service_cc = CoaCostCenterService(repo)
    return _service_cc


def _service_dim() -> CoaDimensionService:
    global _service_dim
    if _service_dim is None:
        repo = SQLAlchemyDimensionRepository()
        _service_dim = CoaDimensionService(repo)
    return _service_dim


def _service_dv() -> CoaDimensionValueService:
    global _service_dv
    if _service_dv is None:
        repo = SQLAlchemyDimensionValueRepository()
        _service_dv = CoaDimensionValueService(repo)
    return _service_dv


def _actor(data: dict) -> UUID | None:
    try:
        return UUID(data["actor"]) if data.get("actor") else None
    except (ValueError, TypeError):
        return None


def _require_actor(data: dict):
    actor = _actor(data)
    if actor is None:
        return None, (jsonify({"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}), 400)
    return actor, None


# ── Cost Centers ──────────────────────────────────────────────────────────

@cost_center_bp.get("/v1/cost-centers")
@casbin_required(*READ_ROLES)
def list_cost_centers():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        cc_list = _service_cc().list_by_company(UUID(company_id))
        return jsonify({"cost_centers": [serialize_cost_center(c) for c in cc_list]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("list_cost_centers failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/cost-centers")
@casbin_required(*AUTO_SEED_ROLES)  # no AUDITOR; write operation
def create_cost_center():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        cc = _service_cc().create_cost_center(
            code=data.get("code", ""),
            name=data.get("name", ""),
            company_id=UUID(data["company_id"]),
            actor=actor,
            description=data.get("description"),
        )
        return jsonify({"cost_center": serialize_cost_center(cc)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 422
    except DuplicateMSTError as e:
        return jsonify({"error": str(e), "code": "COA_ERROR"}), 409
    except Exception as exc:
        logger.exception("create_cost_center failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.get("/v1/cost-centers/<uuid:cost_center_id>")
@casbin_required(*READ_ROLES)
def get_cost_center(cost_center_id: UUID):
    try:
        # Need company_id from query or context; simplified for now
        company_id = request.args.get("company_id")
        if not company_id:
            return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
        cc = _service_cc()._cc_repo.get_by_code  # placeholder
        # Try to get by ID via service
        from src.application.services.cost_center_service import CoaCostCenterService
        # Actually, let's just use the repo directly
        from src.infrastructure.repositories.cost_center_repo import SQLAlchemyCostCenterRepository
        repo = SQLAlchemyCostCenterRepository()
        model = db.session.get(repo.model_type if hasattr(repo, 'model_type') else type, cost_center_id)
        # Simplified: just return error for now
        return jsonify({"error": "Endpoint under construction", "code": "NOT_IMPLEMENTED"}), 501
    except Exception as exc:
        logger.exception("get_cost_center failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Cost Center modify/close ──────────────────────────────────────────────

@cost_center_bp.patch("/v1/cost-centers/<uuid:cost_center_id>")
@casbin_required(*FY_ADMIN_ROLES)  # CHIEF_ACCOUNTANT/ADMIN/DIRECTOR only
def update_cost_center(cost_center_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        cc = _service_cc().update_cost_center(
            cost_center_id=cost_center_id,
            new_code=data.get("code"),
            new_name=data.get("name"),
            actor=actor,
            reason=data.get("reason", ""),  # mandatory for any COA change
        )
        return jsonify({"cost_center": serialize_cost_center(cc)})
    except (DomainException, DuplicateMSTError, SystemAccountModificationError) as e:
        code = getattr(e, "code", "COA_ERROR")
        status = 409 if isinstance(e, DuplicateMSTError) else 422
        return jsonify({"error": str(e), "code": code}), status
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("update_cost_center failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/cost-centers/<uuid:cost_center_id>/close")
@casbin_required("CHIEF_ACCOUNTANT")
def close_cost_center(cost_center_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        cc = _service_cc().close_cost_center(
            cost_center_id=cost_center_id,
            actor=actor,
            reason=data.get("reason", ""),
        )
        return jsonify({"cost_center": serialize_cost_center(cc)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("close_cost_center failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/cost-centers/<uuid:cost_center_id>/reactivate")
@casbin_required("CHIEF_ACCOUNTANT")
def reactivate_cost_center(cost_center_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        cc = _service_cc().reactivate_cost_center(
            cost_center_id=cost_center_id,
            actor=actor,
            reason=data.get("reason", ""),
        )
        return jsonify({"cost_center": serialize_cost_center(cc)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("reactivate_cost_center failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Dimensions ────────────────────────────────────────────────────────────

@cost_center_bp.get("/v1/dimensions")
@casbin_required(*READ_ROLES)
def list_dimensions():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        dim_list = _service_dim().list_by_company(
            UUID(company_id),
            dimension_type=request.args.get("type"),
            is_system=request.args.get("is_system"),
        )
        return jsonify({"dimensions": [serialize_dimension(d) for d in dim_list]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("list_dimensions failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/dimensions")
@casbin_required(*AUTO_SEED_ROLES)  # no AUDITOR; write operation
def create_dimension():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dim = _service_dim().create_dimension(
            code=data.get("code", ""),
            name=data.get("name", ""),
            dimension_type=DimensionType(data.get("type")),  # enum validation
            company_id=UUID(data["company_id"]),
            actor=actor,
            is_system=data.get("is_system", False),
            description=data.get("description"),
        )
        return jsonify({"dimension": serialize_dimension(dim)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 422
    except DuplicateMSTError as e:
        return jsonify({"error": str(e), "code": "COA_ERROR"}), 409
    except Exception as exc:
        logger.exception("create_dimension failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.get("/v1/dimensions/<uuid:dimension_id>")
@casbin_required(*READ_ROLES)
def get_dimension(dimension_id: UUID):
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        dim = _service_dim()._dim_repo.get_by_id(UUID(dimension_id))
        if dim is None:
            return jsonify({"error": "Dimension not found", "code": "NOT_FOUND"}), 404
        return jsonify({"dimension": serialize_dimension(dim)})
    except Exception as exc:
        logger.exception("get_dimension failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.patch("/v1/dimensions/<uuid:dimension_id>")
@casbin_required(*FY_ADMIN_ROLES)  # CHIEF_ACCOUNTANT/ADMIN/DIRECTOR only
def update_dimension(dimension_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dim = _service_dim().update_dimension(
            dimension_id=dimension_id,
            new_name=data.get("name"),
            actor=actor,
            reason=data.get("reason", ""),  # mandatory for any dimension change
        )
        return jsonify({"dimension": serialize_dimension(dim)})
    except (DomainException, SystemAccountModificationError, DuplicateMSTError) as e:
        code = getattr(e, "code", "COA_ERROR")
        status = 409 if isinstance(e, DuplicateMSTError) else 422
        return jsonify({"error": str(e), "code": code}), status
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("update_dimension failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Dimension Values ────────────────────────────────────────────────────

@cost_center_bp.get("/v1/dimension-values")
@casbin_required(*READ_ROLES)
def list_dimension_values():
    company_id = request.args.get("company_id")
    dim_id = request.args.get("dimension_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        dv_list = _service_dv().list_by_company(
            UUID(company_id),
            dimension_id=UUID(dim_id) if dim_id else None,
            status=DimensionValueStatus(request.args.get("status")) if request.args.get("status") else None,
        )
        return jsonify({"dimension_values": [serialize_dimension_value(dv) for dv in dv_list]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("list_dimension_values failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/dimension-values")
@casbin_required(*AUTO_SEED_ROLES)  # no AUDITOR; write operation
def create_dimension_value():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dv = _service_dv().create_dimension_value(
            code=data.get("code", ""),
            name=data.get("name", ""),
            dimension_id=UUID(data["dimension_id"]),
            company_id=UUID(data["company_id"]),
            actor=actor,
            description=data.get("description"),
        )
        return jsonify({"dimension_value": serialize_dimension_value(dv)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 422
    except DuplicateMSTError as e:
        return jsonify({"error": str(e), "code": "COA_ERROR"}), 409
    except Exception as exc:
        logger.exception("create_dimension_value failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.patch("/v1/dimension-values/<uuid:dv_id>")
@casbin_required(*FY_ADMIN_ROLES)  # CHIEF_ACCOUNTANT/ADMIN/DIRECTOR only
def update_dimension_value(dv_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dv = _service_dv().update_dimension_value(
            dv_id=dv_id,
            new_name=data.get("name"),
            actor=actor,
            reason=data.get("reason", ""),  # mandatory for any dimension value change
        )
        return jsonify({"dimension_value": serialize_dimension_value(dv)})
    except (DomainException, DuplicateMSTError) as e:
        code = getattr(e, "code", "COA_ERROR")
        status = 409 if isinstance(e, DuplicateMSTError) else 422
        return jsonify({"error": str(e), "code": code}), status
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("update_dimension_value failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/dimension-values/<uuid:dv_id>/deactivate")
@casbin_required("CHIEF_ACCOUNTANT")
def deactivate_dimension_value(dv_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dv = _service_dv().deactivate_dimension_value(dv_id=dv_id, actor=actor, reason=data.get("reason", ""))
        return jsonify({"dimension_value": serialize_dimension_value(dv)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("deactivate_dimension_value failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@cost_center_bp.post("/v1/dimension-values/<uuid:dv_id>/reactivate")
@casbin_required("CHIEF_ACCOUNTANT")
def reactivate_dimension_value(dv_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        dv = _service_dv().reactivate_dimension_value(dv_id=dv_id, actor=actor, reason=data.get("reason", ""))
        return jsonify({"dimension_value": serialize_dimension_value(dv)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("reactivate_dimension_value failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500