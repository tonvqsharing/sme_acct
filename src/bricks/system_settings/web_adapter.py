"""System settings web adapter — read-heavy; writes SOD-gated."""

from __future__ import annotations

from datetime import date as _date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.system_settings.domain import FlagLockedError
from src.bricks.system_settings.services import (
    ConfigVersionConflictError,
    DuplicateSeriesPrefixError,
    InvalidPeriodError,
    MaxSeriesExceededError,
    SodViolationError,
)

settings_bp = Blueprint("system_settings", __name__)

_settings_service: Any = None


def init_settings_service(svc: Any) -> None:
    global _settings_service
    _settings_service = svc


def _svc() -> Any:
    s = _settings_service
    if s is None:
        abort(500, description="SystemSettingsService not initialized")
    return s


ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN")
CONFIG_UPDATE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "ACCOUNTANT")


@settings_bp.get("/api/v1/system-settings/tax-rates")
@login_required  # type: ignore[untyped-decorator]
def list_tax_rates() -> tuple[Any, int]:
    return (
        jsonify(
            {
                "data": [
                    {"name": r.name, "percent": r.value, "fraction": float(r.to_fraction())}
                    for r in __import__(
                        "src.bricks.system_settings.domain", fromlist=["TaxRate"]
                    ).TaxRate
                ]
            }
        ),
        200,
    )


@settings_bp.get("/api/v1/system-settings/config/<cid>")
@login_required  # type: ignore[untyped-decorator]
def get_config(cid: str) -> tuple[Any, int]:
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    cfg = _svc().get_config(cid_u)
    return (
        jsonify(
            {
                "data": {
                    "company_id": str(cfg.company_id),
                    "vat_rates": sorted(cfg.vat_rates),
                    "e_invoice_series": [
                        {
                            "prefix": x.prefix,
                            "active": x.active,
                            "next_sequence": x.next_sequence,
                            "ca_signer": x.ca_signer,
                        }
                        for x in sorted(cfg.e_invoice_series, key=lambda s: s.prefix)
                    ],
                    "config_version": cfg.config_version,
                    "fiscal_year_start_month": cfg.fiscal_year_start_month,
                    "fiscal_year_start_day": cfg.fiscal_year_start_day,
                    "vat_settlement_cycle": cfg.vat_settlement_cycle,
                    "decimal_places": cfg.decimal_places,
                    "default_currency": cfg.default_currency,
                    "cost_center_required": cfg.cost_center_required,
                    "legal_reviewed_at": (
                        cfg.legal_reviewed_at.isoformat() if cfg.legal_reviewed_at else None
                    ),
                    "legal_reviewed_by": (
                        str(cfg.legal_reviewed_by) if cfg.legal_reviewed_by else None
                    ),
                }
            }
        ),
        200,
    )


@settings_bp.patch("/api/v1/system-settings/config/<cid>/flags/<flag_name>")
@login_required  # type: ignore[untyped-decorator]
def update_config_flag(cid: str, flag_name: str) -> tuple[Any, int]:
    """Update a CONFIG-type flag."""
    role = getattr(current_user, "role", "")
    if role not in CONFIG_UPDATE_ROLES:
        abort(403)
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    body = request.get_json(silent=True) or {}
    if "value" not in body:
        abort(422, description="Missing 'value'")
    try:
        config_version = int(body.get("config_version", 0))
    except (TypeError, ValueError):
        abort(422, description="config_version must be integer")
    try:
        cfg = _svc().update_config_flag(
            cid_u, flag_name, body["value"], UUID(str(current_user.id)), config_version
        )
    except FlagLockedError as exc:
        return jsonify({"error": str(exc), "code": "FLAG_LOCKED"}), 403
    except ConfigVersionConflictError as exc:
        return jsonify({"error": str(exc), "code": "CONFIG_VERSION_CONFLICT"}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_FLAG_VALUE"}), 422
    return jsonify({"data": {"config_version": cfg.config_version}}), 200


@settings_bp.post("/api/v1/system-settings/config/<cid>/legal-review")
@login_required  # type: ignore[untyped-decorator]
def legal_review(cid: str) -> tuple[Any, int]:
    """Mark config as legally reviewed by Chief Accountant."""
    role = getattr(current_user, "role", "")
    if role != "CHIEF_ACCOUNTANT":
        abort(403)
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    cfg = _svc().legal_review(cid_u, UUID(str(current_user.id)))
    return (
        jsonify(
            {
                "data": {
                    "config_version": cfg.config_version,
                    "legal_reviewed_at": (
                        cfg.legal_reviewed_at.isoformat() if cfg.legal_reviewed_at else None
                    ),
                    "legal_reviewed_by": (
                        str(cfg.legal_reviewed_by) if cfg.legal_reviewed_by else None
                    ),
                }
            }
        ),
        200,
    )


# ─── Period lock endpoints (P0-02) ──────────────────────────────────────


@settings_bp.post("/api/v1/system-settings/config/<cid>/period/lock")
@login_required  # type: ignore[untyped-decorator]
def lock_period(cid: str) -> tuple[Any, int]:
    """Lock a specific accounting period."""
    role = getattr(current_user, "role", "")
    if role not in ("ACCOUNTANT", "ADMIN", "CHIEF_ACCOUNTANT"):
        abort(403)
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    body = request.get_json(silent=True) or {}
    try:
        fiscal_year = int(body["fiscal_year"])
        period = int(body["period"])
    except (KeyError, TypeError, ValueError) as exc:
        abort(422, description=f"Missing or invalid: {exc}")
    if fiscal_year < 1:
        abort(422, description="fiscal_year must be positive")
    notes = body.get("notes")
    try:
        _svc().lock_period(cid_u, fiscal_year, period, UUID(str(current_user.id)), notes)
    except InvalidPeriodError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PERIOD"}), 422
    return jsonify({"data": {"locked": True, "fiscal_year": fiscal_year, "period": period}}), 200


@settings_bp.post("/api/v1/system-settings/config/<cid>/period/unlock")
@login_required  # type: ignore[untyped-decorator]
def unlock_period(cid: str) -> tuple[Any, int]:
    """Unlock a specific accounting period."""
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        abort(403)
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    body = request.get_json(silent=True) or {}
    try:
        fiscal_year = int(body["fiscal_year"])
        period = int(body["period"])
    except (KeyError, TypeError, ValueError) as exc:
        abort(422, description=f"Missing or invalid: {exc}")
    was_locked = _svc().unlock_period(cid_u, fiscal_year, period)
    return (
        jsonify({"data": {"unlocked": was_locked, "fiscal_year": fiscal_year, "period": period}}),
        200,
    )


@settings_bp.get("/api/v1/system-settings/config/<cid>/period/status")
@login_required  # type: ignore[untyped-decorator]
def period_status(cid: str) -> tuple[Any, int]:
    """Get period lock status for a company."""
    try:
        cid_u = UUID(cid)
    except ValueError:
        abort(422, description="Invalid UUID")
    fiscal_year = request.args.get("fiscal_year")
    fy_int = None
    if fiscal_year:
        try:
            fy_int = int(fiscal_year)
        except (TypeError, ValueError):
            abort(422, description="fiscal_year must be integer")
    locked = _svc().list_locked_periods(cid_u, fy_int)
    return jsonify({"data": locked}), 200


# ─── E-invoice series endpoints ──────────────────────────────────────────


@settings_bp.post("/api/v1/system-settings/e-invoice-series")
@login_required  # type: ignore[untyped-decorator]
def add_e_invoice_series() -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in ADMIN_ROLES:
        abort(403)
    body = request.get_json(silent=True) or {}
    try:
        approver_raw = body["approver"]
        actor = UUID(str(current_user.id))
        new = _svc().add_e_invoice_series(
            UUID(body["company_id"]),
            actor=actor,
            prefix=body.get("prefix", ""),
            ca_signer=body.get("ca_signer"),
            approver=UUID(str(approver_raw)),
        )
    except KeyError as exc:
        abort(422, description=f"missing {exc}")
    except SodViolationError as exc:
        return jsonify({"error": str(exc), "code": "SOD_VIOLATION"}), 403
    except MaxSeriesExceededError as exc:
        return jsonify({"error": str(exc), "code": "MAX_SERIES_EXCEEDED"}), 409
    except DuplicateSeriesPrefixError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_SERIES_PREFIX"}), 409
    return (
        jsonify(
            {
                "data": {
                    "prefix": new.prefix,
                    "ca_signer": new.ca_signer,
                    "next_sequence": new.next_sequence,
                }
            }
        ),
        201,
    )


# ─── VAT declaration (read-only, specs-vat-declaration.md) ─────────────────

_vat_decl_service: Any = None


def init_vat_declaration_service(svc: Any) -> None:
    global _vat_decl_service
    _vat_decl_service = svc


def _dec(v: Any) -> float:
    return float(v)


@settings_bp.get("/api/v1/reports/vat-declaration")
@login_required  # type: ignore[untyped-decorator]
def vat_declaration() -> tuple[Any, int]:
    if _vat_decl_service is None:
        abort(500, description="VatDeclarationService not initialized")
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
        year = int(args.get("year", ""))
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    month_raw, quarter_raw = args.get("month"), args.get("quarter")
    try:
        month = int(month_raw) if month_raw else None
        quarter = int(quarter_raw) if quarter_raw else None
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    try:
        if quarter is not None:
            d = _vat_decl_service.declare(cid, year, quarter=quarter)
        else:
            d = _vat_decl_service.declare(cid, year, month=month or 0)
    except InvalidPeriodError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PERIOD"}), 422
    payload = {
        "period": d["period"],
        "output_vat": _dec(d["output_vat"]),
        "input_vat_deductible": _dec(d["input_vat_deductible"]),
        "vat_payable": _dec(d["vat_payable"]),
        "carry_forward": _dec(d["carry_forward"]),
        "detail": d["detail"],
    }
    return jsonify({"data": payload}), 200


# ─── Tax-rate windows master data ──────────────────────────────────────────

_catalog_service: Any = None


def init_tax_rate_catalog_service(svc: Any) -> None:
    global _catalog_service
    _catalog_service = svc


def _catalog() -> Any:
    s = _catalog_service
    if s is None:
        abort(500, description="TaxRateCatalogService not initialized")
    return s


def _ser_window(w: Any) -> dict[str, Any]:
    return {
        "rate_pct": w.rate_pct,
        "fraction": w.fraction,
        "valid_from": w.valid_from.isoformat() if w.valid_from else None,
        "valid_to": w.valid_to.isoformat() if w.valid_to else None,
        "decree_ref": w.decree_ref,
        "active_on": None,
    }


@settings_bp.get("/api/v1/tax-rate-windows")
@login_required  # type: ignore[untyped-decorator]
def list_rate_windows() -> tuple[Any, int]:
    on_param = request.args.get("on")
    rows = _catalog().all_windows()
    if on_param:
        from datetime import date as _d

        try:
            on_date = _d.fromisoformat(on_param)
        except ValueError:
            abort(422, description="invalid 'on' date")
        rows = [w for w in rows if w.covers(on_date)]
        return jsonify({"data": [{**_ser_window(w), "active_on": on_param} for w in rows]}), 200
    return jsonify({"data": [_ser_window(w) for w in rows]}), 200


@settings_bp.post("/api/v1/tax-rate-windows")
@login_required  # type: ignore[untyped-decorator]
def add_rate_window() -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in ADMIN_ROLES:
        abort(403)
    body = request.get_json(silent=True) or {}
    try:
        w = __import__(
            "src.bricks.system_settings.rate_windows",
            fromlist=["TaxRateWindow"],
        ).TaxRateWindow(
            rate_pct=int(body["rate_pct"]),
            fraction=str(body["fraction"]),
            valid_from=_date.fromisoformat(body["valid_from"]) if body.get("valid_from") else None,
            valid_to=_date.fromisoformat(body["valid_to"]) if body.get("valid_to") else None,
            decree_ref=body.get("decree_ref", ""),
        )
        out = _catalog().add_window(
            w,
            actor=UUID(str(current_user.id)),
            approver=UUID(str(body["approver"])),
        )
    except KeyError as exc:
        abort(422, description=f"missing {exc}")
    except SodViolationError as exc:
        return jsonify({"error": str(exc), "code": "SOD_VIOLATION"}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "OVERLAPPING_WINDOW"}), 409
    return jsonify({"data": _ser_window(out)}), 201
