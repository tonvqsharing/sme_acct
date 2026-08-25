"""System settings web adapter — read-heavy; writes SOD-gated."""

from __future__ import annotations

from datetime import date as _date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.system_settings.services import (
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
                }
            }
        ),
        200,
    )


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
