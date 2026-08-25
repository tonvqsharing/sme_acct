"""System settings web adapter — read-heavy; writes SOD-gated."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.system_settings.services import (
    DuplicateSeriesPrefixError,
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
