"""Inventory web adapter — Tryton stock parity, TT99 compliant."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.inventory.services import (
    DuplicateProductCodeError,
    InsufficientStockError,
    NoOpenPeriodError,
    NotFoundError,
    PeriodClosedError,
)

inventory_bp = Blueprint("inventory", __name__)

_inv_service: Any = None


def init_inventory_service(svc: Any) -> None:
    global _inv_service
    _inv_service = svc


def _svc() -> Any:
    s = _inv_service
    if s is None:
        abort(500, description="InventoryService not initialized")
    return s


def _require_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in ("ADMIN", "ACCOUNTANT", "CHIEF_ACCOUNTANT", "DIRECTOR"):
        abort(403)


# ── products ──
@inventory_bp.post("/api/v1/inventory/products")
@login_required  # type: ignore[untyped-decorator]
def create_product() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        p = _svc().create_product(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            uom=body.get("uom", "Cái"),
            cost_method=body.get("cost_method", "wavg"),
            standard_cost=body.get("standard_cost"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create product",
        )
    except DuplicateProductCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_SKU"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PRODUCT"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(p.id),
                    "code": p.code,
                    "name": p.name,
                    "uom": p.uom,
                    "cost_method": p.cost_method.value,
                    "standard_cost": str(p.standard_cost) if p.standard_cost else None,
                }
            }
        ),
        201,
    )


@inventory_bp.get("/api/v1/inventory/products")
@login_required  # type: ignore[untyped-decorator]
def list_products() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_products(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "uom": r.uom,
                        "cost_method": r.cost_method.value,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── locations ──
@inventory_bp.post("/api/v1/inventory/locations")
@login_required  # type: ignore[untyped-decorator]
def create_location() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        loc = _svc().create_location(
            company_id=UUID(body["company_id"]),
            warehouse_id=UUID(body["warehouse_id"]) if body.get("warehouse_id") else None,
            code=body["code"],
            name=body.get("name", ""),
            type=body.get("type", "shelf"),
            parent_id=UUID(body["parent_id"]) if body.get("parent_id") else None,
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_LOCATION"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(loc.id),
                    "code": loc.code,
                    "name": loc.name,
                    "type": loc.type.value,
                }
            }
        ),
        201,
    )


@inventory_bp.get("/api/v1/inventory/locations")
@login_required  # type: ignore[untyped-decorator]
def list_locations() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_locations(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "type": r.type.value,
                        "warehouse_id": str(r.warehouse_id) if r.warehouse_id else None,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── category ──
@inventory_bp.post("/api/v1/inventory/categories")
@login_required  # type: ignore[untyped-decorator]
def create_category() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        cat = _svc().create_category(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            parent_id=UUID(body["parent_id"]) if body.get("parent_id") else None,
            cost_method=body.get("cost_method"),
            account_code=body.get("account_code"),
            tax_category=body.get("tax_category"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create category",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CATEGORY"}), 422
    return jsonify({"data": {"id": str(cat.id), "code": cat.code, "name": cat.name}}), 201


@inventory_bp.get("/api/v1/inventory/categories")
@login_required  # type: ignore[untyped-decorator]
def list_categories() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_categories(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "cost_method": r.cost_method.value if r.cost_method else None,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── warehouse ──
@inventory_bp.post("/api/v1/inventory/warehouses")
@login_required  # type: ignore[untyped-decorator]
def create_warehouse() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        wh = _svc().create_warehouse(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            address=body.get("address"),
            manager_id=UUID(body["manager_id"]) if body.get("manager_id") else None,
            account_code=body.get("account_code"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create warehouse",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_WAREHOUSE"}), 422
    return jsonify({"data": {"id": str(wh.id), "code": wh.code, "name": wh.name}}), 201


@inventory_bp.get("/api/v1/inventory/warehouses")
@login_required  # type: ignore[untyped-decorator]
def list_warehouses() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_warehouses(cid)
    return (
        jsonify(
            {
                "data": [
                    {"id": str(r.id), "code": r.code, "name": r.name, "address": r.address}
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── lots ──
@inventory_bp.post("/api/v1/inventory/lots")
@login_required  # type: ignore[untyped-decorator]
def create_lot() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        lot = _svc().create_lot(
            company_id=UUID(body["company_id"]),
            product_id=UUID(body["product_id"]),
            lot_code=body["lot_code"],
            expiry_date=(
                date.fromisoformat(body["expiry_date"]) if body.get("expiry_date") else None
            ),
            qty=body.get("qty", "0"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create lot",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_LOT"}), 422
    return (
        jsonify({"data": {"id": str(lot.id), "lot_code": lot.lot_code, "qty": str(lot.qty)}}),
        201,
    )


@inventory_bp.get("/api/v1/inventory/lots")
@login_required  # type: ignore[untyped-decorator]
def list_lots() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    pid = UUID(request.args["product_id"]) if request.args.get("product_id") else None
    rows = _svc().list_lots(cid, pid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "lot_code": r.lot_code,
                        "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
                        "qty": str(r.qty),
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── price lists ──
@inventory_bp.post("/api/v1/inventory/price-lists")
@login_required  # type: ignore[untyped-decorator]
def create_price() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        pl = _svc().create_price(
            company_id=UUID(body["company_id"]),
            product_id=UUID(body["product_id"]),
            uom_id=UUID(body["uom_id"]) if body.get("uom_id") else None,
            price=body.get("price", "0"),
            valid_from=date.fromisoformat(body["valid_from"]) if body.get("valid_from") else None,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create price",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PRICE"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(pl.id),
                    "price": str(pl.price),
                    "valid_from": pl.valid_from.isoformat(),
                }
            }
        ),
        201,
    )


@inventory_bp.get("/api/v1/inventory/price-lists")
@login_required  # type: ignore[untyped-decorator]
def list_prices() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    pid = UUID(request.args["product_id"]) if request.args.get("product_id") else None
    rows = _svc().list_prices(cid, pid)
    return (
        jsonify(
            {
                "data": [
                    {"id": str(r.id), "price": str(r.price), "valid_from": r.valid_from.isoformat()}
                    for r in rows
                ]
            }
        ),
        200,
    )


# ── shipments ──
@inventory_bp.post("/api/v1/inventory/shipments")
@login_required  # type: ignore[untyped-decorator]
def create_shipment() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        ship = _svc().create_shipment(
            company_id=UUID(body["company_id"]),
            type=body["type"],
            moves=body.get("moves", []),
            effective_date=(
                date.fromisoformat(body["effective_date"]) if body.get("effective_date") else None
            ),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create shipment",
        )
    except (NoOpenPeriodError, PeriodClosedError) as exc:
        return jsonify({"error": str(exc), "code": "NO_OPEN_PERIOD"}), 409
    except (NotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_SHIPMENT"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(ship.id),
                    "number": ship.number,
                    "type": ship.type.value,
                    "state": ship.state.value,
                    "moves": [str(x) for x in ship.moves],
                }
            }
        ),
        201,
    )


@inventory_bp.post("/api/v1/inventory/shipments/<sid>/post")
@login_required  # type: ignore[untyped-decorator]
def post_shipment(sid: str) -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        ship_id = UUID(sid)
    except ValueError:
        abort(422, description="Invalid UUID")
    try:
        ship = _svc().post_shipment(
            ship_id, actor=UUID(str(current_user.id)), reason=body.get("reason") or "post"
        )
    except NotFoundError:
        abort(404, description="shipment not found")
    except InsufficientStockError as exc:
        return jsonify({"error": str(exc), "code": "INSUFFICIENT_STOCK"}), 409
    except (NoOpenPeriodError, PeriodClosedError) as exc:
        return jsonify({"error": str(exc), "code": "NO_OPEN_PERIOD"}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_SHIPMENT"}), 422
    return (
        jsonify({"data": {"id": str(ship.id), "number": ship.number, "state": ship.state.value}}),
        200,
    )


@inventory_bp.get("/api/v1/inventory/shipments/<sid>")
@login_required  # type: ignore[untyped-decorator]
def get_shipment(sid: str) -> tuple[Any, int]:
    try:
        ship = _svc()._repo.get_shipment(UUID(sid))
    except ValueError:
        abort(422, description="Invalid UUID")
    if not ship:
        abort(404, description="shipment not found")
    return (
        jsonify(
            {
                "data": {
                    "id": str(ship.id),
                    "number": ship.number,
                    "type": ship.type.value,
                    "state": ship.state.value,
                    "moves": [str(x) for x in ship.moves],
                }
            }
        ),
        200,
    )


# ── stock & reports ──
@inventory_bp.get("/api/v1/inventory/stock")
@login_required  # type: ignore[untyped-decorator]
def get_stock() -> tuple[Any, int]:
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    product_id = UUID(args["product_id"]) if args.get("product_id") else None
    warehouse_id = UUID(args["warehouse_id"]) if args.get("warehouse_id") else None
    rows = _svc().get_stock(cid, product_id=product_id, warehouse_id=warehouse_id)
    return jsonify({"data": rows}), 200


@inventory_bp.get("/api/v1/reports/inventory/nxt")
@login_required  # type: ignore[untyped-decorator]
def nxt_report() -> tuple[Any, int]:
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
        from_date = date.fromisoformat(args.get("from", ""))
        to_date = date.fromisoformat(args.get("to", ""))
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    rows = _svc().nxt_report(cid, from_date, to_date)
    return jsonify({"data": rows}), 200


@inventory_bp.get("/api/v1/reports/inventory/turnover")
@login_required  # type: ignore[untyped-decorator]
def turnover_report() -> tuple[Any, int]:
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
        from_date = date.fromisoformat(args.get("from", ""))
        to_date = date.fromisoformat(args.get("to", ""))
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    rows = _svc().turnover(cid, from_date, to_date)
    return jsonify({"data": rows}), 200


@inventory_bp.post("/api/v1/inventory/count")
@login_required  # type: ignore[untyped-decorator]
def count_inventory() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        ship = _svc().count_inventory(
            company_id=UUID(body["company_id"]),
            location_id=UUID(body["location_id"]),
            counts=body.get("counts", []),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "count",
        )
    except (NotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_COUNT"}), 422
    return (
        jsonify({"data": {"id": str(ship.id), "number": ship.number, "state": ship.state.value}}),
        201,
    )


@inventory_bp.post("/api/v1/inventory/periods/close")
@login_required  # type: ignore[untyped-decorator]
def close_period() -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        return jsonify({"error": "Only CHIEF/ADMIN can close period", "code": "SOD_VIOLATION"}), 403
    body = request.get_json(silent=True) or {}
    try:
        _svc().close_period(
            company_id=UUID(body["company_id"]),
            year=int(body["year"]),
            month=int(body["month"]),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "close",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PERIOD"}), 422
    return jsonify({"data": {"closed": True}}), 200
