"""Opening balance web adapter — ONLY Flask file in brick."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.opening_balance.services import (
    BatchLockedError,
    NotFoundError,
    UnbalancedOpeningError,
)

opening_balance_bp = Blueprint("opening_balance", __name__)

_opening_service: Any = None


def init_opening_service(svc: Any) -> None:
    global _opening_service
    _opening_service = svc


def _svc() -> Any:
    s = _opening_service
    if s is None:
        abort(500, description="OpeningService not initialized")
    return s


def _require_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in ("ADMIN", "ACCOUNTANT", "CHIEF_ACCOUNTANT", "DIRECTOR"):
        abort(403)


def _require_chief() -> None:
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        abort(403, description="Only CHIEF_ACCOUNTANT/ADMIN")


@opening_balance_bp.post("/api/v1/opening-batches")
@login_required  # type: ignore[untyped-decorator]
def create_batch() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        b = _svc().create_batch(
            company_id=UUID(body["company_id"]),
            fiscal_year_id=UUID(body["fiscal_year_id"]),
            source=body.get("source", "MANUAL"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create opening batch",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_BATCH"}), 422
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return jsonify({"data": {"id": str(b.id), "state": b.state.value}}), 201


@opening_balance_bp.post("/api/v1/opening-batches/<bid>/gl")
@login_required  # type: ignore[untyped-decorator]
def post_gl(bid: str) -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        bid_u = UUID(bid)
    except ValueError:
        abort(422, description="Invalid UUID")
    try:
        _svc().post_gl(
            bid_u,
            lines=body.get("lines", []),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "post gl opening",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_GL"}), 422
    except BatchLockedError as exc:
        return jsonify({"error": str(exc), "code": "BATCH_LOCKED"}), 409
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return jsonify({"data": {"posted": True}}), 201


@opening_balance_bp.post("/api/v1/opening-batches/<bid>/bank")
@login_required  # type: ignore[untyped-decorator]
def post_bank(bid: str) -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        bid_u = UUID(bid)
    except ValueError:
        abort(422, description="Invalid UUID")
    try:
        _svc().post_bank(
            bid_u,
            rows=body.get("rows", []),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "post bank opening",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_BANK"}), 422
    except BatchLockedError as exc:
        return jsonify({"error": str(exc), "code": "BATCH_LOCKED"}), 409
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return jsonify({"data": {"posted": True}}), 201


@opening_balance_bp.get("/api/v1/opening-batches/<bid>/reconcile")
@login_required  # type: ignore[untyped-decorator]
def reconcile(bid: str) -> tuple[Any, int]:
    try:
        bid_u = UUID(bid)
    except ValueError:
        abort(422, description="Invalid UUID")
    try:
        rep = _svc().reconcile(bid_u)
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return (
        jsonify(
            {
                "data": {
                    "balanced": rep["balanced"],
                    "debit_total": float(rep["debit_total"]),
                    "credit_total": float(rep["credit_total"]),
                    "checks": {
                        "bank_total": float(rep["checks"]["bank_total"]),
                        "gl_lines": rep["checks"]["gl_lines"],
                    },
                }
            }
        ),
        200,
    )


@opening_balance_bp.post("/api/v1/opening-batches/<bid>/lock")
@login_required  # type: ignore[untyped-decorator]
def lock(bid: str) -> tuple[Any, int]:
    _require_chief()
    body = request.get_json(silent=True) or {}
    try:
        b = _svc().lock(
            UUID(bid),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "go-live",
        )
    except UnbalancedOpeningError as exc:
        return jsonify({"error": str(exc), "code": "UNBALANCED_OPENING"}), 409
    except BatchLockedError as exc:
        return jsonify({"error": str(exc), "code": "BATCH_LOCKED"}), 409
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return jsonify({"data": {"id": str(b.id), "state": b.state.value}}), 200


@opening_balance_bp.post("/api/v1/opening-batches/<bid>/reopen")
@login_required  # type: ignore[untyped-decorator]
def reopen(bid: str) -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    body = request.get_json(silent=True) or {}
    try:
        b = _svc().reopen(
            UUID(bid),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "reopen",
            is_chief=(role in ("CHIEF_ACCOUNTANT", "ADMIN")),
        )
    except PermissionError as exc:
        return jsonify({"error": str(exc), "code": "SOD_VIOLATION"}), 403
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    return jsonify({"data": {"id": str(b.id), "state": b.state.value}}), 200
