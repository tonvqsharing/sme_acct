"""Payment Terms & Document Numbering web adapters.

Flask blueprints + REST endpoints. ONLY file importing Flask in the brick.
Role matrices + error-code contract per specs-payment-terms.md §6, §12.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.payment_terms.domain import (
    AuditorReadOnlyError,
    DocumentNumberingSeries,
    PaymentTerm,
    PaymentTermsDomainError,
)
from src.bricks.payment_terms.services import (
    DEFAULT_ROLES,
    READ_ROLES,
    WRITE_ROLES,
    DocumentNumberingSeriesService,
    PaymentTermService,
)

logger = logging.getLogger(__name__)

payment_terms_bp = Blueprint("payment_terms", __name__)
document_numbering_bp = Blueprint("document_numbering", __name__)

INCREMENT_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "DIRECTOR")

# ─── Service instances (wired by app factory) ──────────────────────────────

_payment_term_service: PaymentTermService | None = None
_series_service: DocumentNumberingSeriesService | None = None


def init_payment_terms_services(
    term_service: PaymentTermService,
    series_service: DocumentNumberingSeriesService,
) -> None:
    global _payment_term_service, _series_service
    _payment_term_service = term_service
    _series_service = series_service


def _term_service() -> PaymentTermService:
    svc = _payment_term_service
    if svc is None:
        abort(500, description="PaymentTermService not initialized")
    return svc


def _series_service_or_500() -> DocumentNumberingSeriesService:
    svc = _series_service
    if svc is None:
        abort(500, description="DocumentNumberingSeriesService not initialized")
    return svc


# ─── Helpers ───────────────────────────────────────────────────────────────


def _require_roles(allowed: tuple[str, ...]) -> None:
    """Flask built-in RBAC. AUDITOR writes map to EX-007 code.

    Order matters: READ_ROLES includes AUDITOR, so membership is checked
    first; the EX-007 branch only fires on non-read routes.
    """
    role = getattr(current_user, "role", "")
    if not role:
        abort(403, description="Role missing")
    if role in allowed:
        return
    if role == "AUDITOR":
        raise AuditorReadOnlyError("AUDITOR chỉ đọc")
    abort(403, description=f"RBAC denied: requires {('/'.join(allowed))}")


def _body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(422, description="Request body required")
    return data


def _actor_from(body: dict[str, Any]) -> UUID | None:
    raw = body.get("actor")
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def serialize_payment_term(term: PaymentTerm) -> dict[str, Any]:
    return {
        "id": str(term.id),
        "company_id": str(term.company_id),
        "name": term.name,
        "due_days": term.due_days,
        "interest_rate": float(term.interest_rate),
        "is_default": term.is_default,
        "status": term.status.value,
        "created_at": term.created_at.isoformat(),
        "checksum": term.checksum,
    }


def serialize_series(series: DocumentNumberingSeries) -> dict[str, Any]:
    return {
        "id": str(series.id),
        "company_id": str(series.company_id),
        "prefix": series.prefix,
        "next_sequence": series.next_sequence,
        "is_active": series.is_active,
        "max_sequences": series.max_sequences,
        "status": series.status.value,
        "created_at": series.created_at.isoformat(),
        "checksum": series.checksum,
    }


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        abort(422, description="Invalid UUID format")
        raise  # pragma: no cover - abort always raises


# ═══ Payment Terms routes ═════════════════════════════════════════════════


def _require_company(source: dict[str, Any]) -> UUID:
    raw = source.get("company_id", "")
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        abort(422, description="company_id is required")
        raise  # pragma: no cover - abort always raises


@payment_terms_bp.errorhandler(PaymentTermsDomainError)
def _handle_domain_error(exc: PaymentTermsDomainError) -> tuple[Any, int]:
    return jsonify({"error": str(exc), "code": exc.code}), exc.http_status


@payment_terms_bp.get("/api/v1/payment-terms")
@login_required  # type: ignore[untyped-decorator]
def list_payment_terms() -> tuple[Any, int]:
    _require_roles(READ_ROLES)
    status = request.args.get("status")
    company_id = _require_company(request.args)
    terms = _term_service().list_by_company(company_id, status=status)
    return jsonify({"data": [serialize_payment_term(t) for t in terms]}), 200


@payment_terms_bp.post("/api/v1/payment-terms")
@login_required  # type: ignore[untyped-decorator]
def create_payment_term() -> tuple[Any, int]:
    _require_roles(WRITE_ROLES)
    body = _body()
    svc = _term_service()
    term = svc.create_payment_term(
        company_id=_require_company(body),
        name=str(body.get("name", "")),
        due_days=int(body.get("due_days", 30)),
        interest_rate=body.get("interest_rate", 0),
        actor=_actor_from(body),
        reason=body.get("reason"),
        is_default=bool(body.get("is_default", False)),
    )
    logger.info(
        "Payment term created",
        extra={"term_id": str(term.id), "actor": str(_actor_from(body))},
    )
    return jsonify({"data": serialize_payment_term(term)}), 201


@payment_terms_bp.get("/api/v1/payment-terms/<term_id>")
@login_required  # type: ignore[untyped-decorator]
def get_payment_term(term_id: str) -> tuple[Any, int]:
    _require_roles(READ_ROLES)
    term = _term_service().get_payment_term(_parse_uuid(term_id))
    if term is None:
        abort(404, description="Payment term not found")
    return jsonify({"data": serialize_payment_term(term)}), 200


@payment_terms_bp.patch("/api/v1/payment-terms/<term_id>")
@login_required  # type: ignore[untyped-decorator]
def update_payment_term(term_id: str) -> tuple[Any, int]:
    _require_roles(WRITE_ROLES)
    body = _body()
    fields = {k: v for k, v in body.items() if k in ("name", "due_days", "interest_rate")}
    updated = _term_service().update_payment_term(
        _parse_uuid(term_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
        **fields,
    )
    return jsonify({"data": serialize_payment_term(updated)}), 200


@payment_terms_bp.post("/api/v1/payment-terms/<term_id>/set-default")
@login_required  # type: ignore[untyped-decorator]
def set_default_payment_term(term_id: str) -> tuple[Any, int]:
    _require_roles(DEFAULT_ROLES)
    body = _body()
    updated = _term_service().set_default_payment_term(
        _parse_uuid(term_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    logger.info(
        "Payment term set default",
        extra={"term_id": term_id, "actor": str(_actor_from(body))},
    )
    return jsonify({"data": serialize_payment_term(updated)}), 200


@payment_terms_bp.post("/api/v1/payment-terms/<term_id>/deactivate")
@login_required  # type: ignore[untyped-decorator]
def deactivate_payment_term(term_id: str) -> tuple[Any, int]:
    _require_roles(DEFAULT_ROLES)
    body = _body()
    updated = _term_service().deactivate_payment_term(
        _parse_uuid(term_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    return jsonify({"data": serialize_payment_term(updated)}), 200


# ═══ Document Numbering routes ════════════════════════════════════════════


@document_numbering_bp.errorhandler(PaymentTermsDomainError)
def _handle_series_domain_error(exc: PaymentTermsDomainError) -> tuple[Any, int]:
    return jsonify({"error": str(exc), "code": exc.code}), exc.http_status


@document_numbering_bp.get("/api/v1/document-numbering")
@login_required  # type: ignore[untyped-decorator]
def list_series() -> tuple[Any, int]:
    _require_roles(READ_ROLES)
    company_id = _require_company(request.args)
    active_param = request.args.get("active")
    active = None if active_param is None else active_param.lower() == "true"
    rows = _series_service_or_500().list_by_company(company_id, active=active)
    return jsonify({"data": [serialize_series(s) for s in rows]}), 200


@document_numbering_bp.post("/api/v1/document-numbering")
@login_required  # type: ignore[untyped-decorator]
def create_series() -> tuple[Any, int]:
    _require_roles(WRITE_ROLES)
    body = _body()
    series = _series_service_or_500().create_series(
        company_id=_require_company(body),
        prefix=str(body.get("prefix", "")),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    return jsonify({"data": serialize_series(series)}), 201


@document_numbering_bp.get("/api/v1/document-numbering/<series_id>")
@login_required  # type: ignore[untyped-decorator]
def get_series(series_id: str) -> tuple[Any, int]:
    _require_roles(READ_ROLES)
    series = _series_service_or_500().get_series(_parse_uuid(series_id))
    if series is None:
        abort(404, description="Series not found")
    return jsonify({"data": serialize_series(series)}), 200


@document_numbering_bp.patch("/api/v1/document-numbering/<series_id>")
@login_required  # type: ignore[untyped-decorator]
def update_series(series_id: str) -> tuple[Any, int]:
    _require_roles(WRITE_ROLES)
    body = _body()
    fields = {k: v for k, v in body.items() if k == "max_sequences"}
    updated = _series_service_or_500().update_series(
        _parse_uuid(series_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
        **fields,
    )
    return jsonify({"data": serialize_series(updated)}), 200


@document_numbering_bp.post("/api/v1/document-numbering/<series_id>/activate")
@login_required  # type: ignore[untyped-decorator]
def activate_series(series_id: str) -> tuple[Any, int]:
    _require_roles(DEFAULT_ROLES)
    body = _body()
    updated = _series_service_or_500().activate_series(
        _parse_uuid(series_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    return jsonify({"data": serialize_series(updated)}), 200


@document_numbering_bp.post("/api/v1/document-numbering/<series_id>/deactivate")
@login_required  # type: ignore[untyped-decorator]
def deactivate_series_route(series_id: str) -> tuple[Any, int]:
    _require_roles(DEFAULT_ROLES)
    body = _body()
    updated = _series_service_or_500().deactivate_series(
        _parse_uuid(series_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    return jsonify({"data": serialize_series(updated)}), 200


@document_numbering_bp.post("/api/v1/document-numbering/<series_id>/increment")
@login_required  # type: ignore[untyped-decorator]
def increment_sequence(series_id: str) -> tuple[Any, int]:
    """HP-004: issue next document number atomically."""
    _require_roles(INCREMENT_ROLES)
    body = _body()
    svc = _series_service_or_500()
    sid = _parse_uuid(series_id)
    sequence_used = svc.increment_sequence(
        sid,
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    series = svc.get_series(sid)
    assert series is not None
    document_number = f"{series.prefix}{sequence_used:06d}"
    return (
        jsonify(
            {
                "data": {
                    "series_id": str(sid),
                    "sequence_used": sequence_used,
                    "document_number": document_number,
                }
            }
        ),
        200,
    )


# ═══ SOD approval routes ══════════════════════════════════════════════════

_approval_service: Any = None


def init_approval_service(service: Any) -> None:
    global _approval_service
    _approval_service = service


def _approvals() -> Any:
    svc = _approval_service
    if svc is None:
        abort(500, description="ApprovalService not initialized")
    return svc


def _serialize_request(req: Any) -> dict[str, Any]:
    return {
        "id": str(req.id),
        "company_id": str(req.company_id),
        "request_type": req.request_type.value,
        "target_id": str(req.target_id),
        "requested_by": str(req.requested_by),
        "reason": req.reason,
        "status": req.status.value,
        "decided_by": str(req.decided_by) if req.decided_by else None,
        "checksum": req.checksum,
    }


@payment_terms_bp.post("/api/v1/approval-requests/set-default/<term_id>")
@login_required  # type: ignore[untyped-decorator]
def request_set_default(term_id: str) -> tuple[Any, int]:
    """§11.1 step 1 — creates PENDING request, does NOT flip default."""
    _require_roles(DEFAULT_ROLES)
    body = _body()
    req = _approvals().request_set_default(
        _parse_uuid(term_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    return jsonify({"data": _serialize_request(req)}), 202


@payment_terms_bp.post("/api/v1/approval-requests/activate-series/<series_id>")
@login_required  # type: ignore[untyped-decorator]
def request_activate_series(series_id: str) -> tuple[Any, int]:
    _require_roles(DEFAULT_ROLES)
    body = _body()
    req = _approvals().request_activate_series(
        _parse_uuid(series_id),
        actor=_actor_from(body),
        reason=body.get("reason"),
    )
    if req is None:
        return jsonify({"data": {"status": "already_active"}}), 200
    return jsonify({"data": _serialize_request(req)}), 202


@payment_terms_bp.get("/api/v1/approval-requests")
@login_required  # type: ignore[untyped-decorator]
def list_approval_requests() -> tuple[Any, int]:
    _require_roles(READ_ROLES)
    status = request.args.get("status")
    rows = _approvals().list_requests(status=status)
    return jsonify({"data": [_serialize_request(r) for r in rows]}), 200


@payment_terms_bp.post("/api/v1/approval-requests/<request_id>/approve")
@login_required  # type: ignore[untyped-decorator]
def approve_request(request_id: str) -> tuple[Any, int]:
    """§11.1/§11.2 step 2 — second actor approves; effect applied."""
    _require_roles(WRITE_ROLES)
    body = _body()
    saved = _approvals().decide(
        _parse_uuid(request_id),
        approver=_actor_from(body),
        reason=body.get("reason"),
        approve=True,
    )
    resp = {"data": _serialize_request(saved)}
    if saved.status.value == "APPROVED" and saved.request_type.value == "SET_DEFAULT":
        term = _term_service().get_payment_term(saved.target_id)
        assert term is not None
        resp["data"]["applied"] = serialize_payment_term(term)
    return jsonify(resp), 200


@payment_terms_bp.post("/api/v1/approval-requests/<request_id>/reject")
@login_required  # type: ignore[untyped-decorator]
def reject_request(request_id: str) -> tuple[Any, int]:
    _require_roles(WRITE_ROLES)
    body = _body()
    saved = _approvals().decide(
        _parse_uuid(request_id),
        approver=_actor_from(body),
        reason=body.get("reason"),
        approve=False,
    )
    return (
        jsonify(
            {
                "error": "Rejected, default unchanged",
                "code": "REQUEST_REJECTED",
                "data": _serialize_request(saved),
            }
        ),
        409,
    )
