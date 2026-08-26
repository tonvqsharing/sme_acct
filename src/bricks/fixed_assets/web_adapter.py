"""Fixed assets web adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.fixed_assets.services import (
    DuplicateAssetCodeError,
)

fixed_assets_bp = Blueprint("fixed_assets", __name__)

_fa_service: Any = None


def init_fixed_assets_service(svc: Any) -> None:
    global _fa_service
    _fa_service = svc


def _svc() -> Any:
    s = _fa_service
    if s is None:
        abort(500, description="FixedAssetService not initialized")
    return s


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")


def _write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in WRITE_ROLES:
        abort(403)


def ser_fa(a: Any) -> dict[str, Any]:

    return {
        "id": str(a.id),
        "asset_code": a.asset_code,
        "name": a.name,
        "category": a.category,
        "original_cost": float(a.original_cost),
        "accumulated_depreciation": float(a.accumulated_depreciation),
        "book_value": float(a.book_value),
        "monthly_depreciation": float(a.monthly_depreciation),
        "useful_life_months": a.useful_life_months,
        "acquisition_date": a.acquisition_date.isoformat(),
        "depreciation_account": a.depreciation_account,
        "is_active": a.is_active,
        "checksum": a.checksum,
    }


@fixed_assets_bp.get("/api/v1/fixed-assets")
@login_required  # type: ignore[untyped-decorator]
def list_fixed_assets() -> tuple[Any, int]:
    cid_raw = request.args.get("company_id", "")
    try:
        cid = UUID(cid_raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_by_company(cid)
    return jsonify({"data": [ser_fa(a) for a in rows]}), 200


@fixed_assets_bp.post("/api/v1/fixed-assets")
@login_required  # type: ignore[untyped-decorator]
def create_fixed_asset() -> tuple[Any, int]:
    _write()
    body = request.get_json(silent=True) or {}
    try:
        fa = _svc().create_asset(
            company_id=UUID(body["company_id"]),
            asset_code=body["asset_code"],
            name=body.get("name", ""),
            category=body.get("category", "huu_hinh"),
            original_cost=Decimal(str(body["original_cost"])),
            acquisition_date=date.fromisoformat(body["acquisition_date"]),
            useful_life_months=int(body["useful_life_months"]),
            depreciation_account=body.get("depreciation_account", "6421"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create FA",
        )
    except DuplicateAssetCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_ASSET_CODE"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_ASSET"}), 422
    return jsonify({"data": ser_fa(fa)}), 201


@fixed_assets_bp.get("/api/v1/fixed-assets/<aid>")
@login_required  # type: ignore[untyped-decorator]
def get_fixed_asset(aid: str) -> tuple[Any, int]:
    try:
        aid_u = UUID(aid)
    except ValueError:
        abort(422, description="Invalid UUID")
    fa = _svc().get_asset(aid_u)
    if fa is None:
        abort(404)
    return jsonify({"data": ser_fa(fa)}), 200


@fixed_assets_bp.post("/api/v1/depreciation-runs/compute")
@login_required  # type: ignore[untyped-decorator]
def compute_depreciation() -> tuple[Any, int]:
    _write()
    body = request.get_json(silent=True) or {}
    try:
        result = _svc().compute_and_post(
            UUID(body["company_id"]),
            actor=UUID(str(current_user.id)),
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_DEP_RUN"}), 422

    for jg in result.get("journal_groups", []):
        jg["total"] = float(jg["total"])
    for e in result.get("entries", []):
        e["amount"] = float(e["amount"])
    return jsonify({"data": result}), 200
