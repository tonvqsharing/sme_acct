"""Inventory service — FY/period gates, per-product cost, 152/632, audit."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.bricks.inventory.costing import (
    fifo_lots_from_moves,
    fifo_out_unit,
    moving_average_unit,
    specific_out_unit,
    split_standard,
)
from src.bricks.inventory.domain import (
    GENESIS_CHECKSUM,
    CostMethod,
    Location,
    LocationType,
    Product,
    Shipment,
    ShipmentType,
    ShipState,
    StockMove,
)


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


class DuplicateProductCodeError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class PeriodClosedError(Exception):
    pass


class NoOpenPeriodError(Exception):
    pass


class InventoryService:
    def __init__(
        self,
        *,
        repo: Any,
        fy: Any,
        numbering: Any,
        audit: Any | None = None,
        voucher_service: Any | None = None,
        coa: Any | None = None,
        regime_of: Any | None = None,
        uom_repo: Any | None = None,
        variance_account_of: Any | None = None,
    ) -> None:
        self._repo = repo
        self._fy = fy
        self._numbering = numbering
        self._audit = audit
        self._voucher = voucher_service
        self._coa = coa
        self._regime_of = regime_of
        self._uom_repo = uom_repo
        self._variance_account_of = variance_account_of

    # ── product ──
    def create_product(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        uom: str,
        cost_method: str,
        standard_cost: Any | None = None,
        uom_id: UUID | None = None,
        category_id: UUID | None = None,
        actor: UUID,
        reason: str,
    ) -> Product:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        if self._repo.get_product_by_code(company_id, code) is not None:
            raise DuplicateProductCodeError(f"SKU {code} đã tồn tại")
        try:
            cm = CostMethod(cost_method)
        except ValueError:
            raise ValueError(f"cost_method {cost_method} invalid (specific/wavg/fifo/standard)")
        std = _d(standard_cost) if standard_cost is not None else None
        if uom_id is not None:
            uom_lookup = None
            if self._uom_repo is not None:
                uom_lookup = self._uom_repo.get_uom(uom_id)
            elif hasattr(self._repo, "get_uom"):
                uom_lookup = self._repo.get_uom(uom_id)
            if uom_lookup is None or uom_lookup.company_id != company_id:
                raise ValueError(f"uom {uom_id} not found in company")
        if category_id is not None:
            cat = self._repo.get_category(category_id)
            if cat is None or cat.company_id != company_id:
                raise ValueError(f"category {category_id} not found in company")
        p = Product(
            company_id=company_id,
            code=code,
            name=name,
            uom=uom,
            cost_method=cm,
            standard_cost=std,
            uom_id=uom_id,
            category_id=category_id,
        )
        p.checksum = p.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        saved = self._repo.create_product(p)
        if self._audit:
            self._audit.append(
                entity_type="inventory_product",
                entity_id=p.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved  # type: ignore[no-any-return]

    def list_products(self, company_id: UUID) -> list[Product]:
        return self._repo.list_products(company_id)  # type: ignore[no-any-return]

    def get_product(self, pid: UUID) -> Product | None:
        return self._repo.get_product(pid)  # type: ignore[no-any-return]

    # ── location ──
    def create_location(
        self,
        *,
        company_id: UUID,
        warehouse_id: UUID | None,
        code: str,
        name: str,
        type: str = "shelf",
        parent_id: UUID | None = None,
        actor: UUID | None = None,
        reason: str | None = None,
    ) -> Location:
        try:
            lt = LocationType(type)
        except ValueError:
            raise ValueError(f"location type {type} invalid")
        loc = Location(
            company_id=company_id,
            warehouse_id=warehouse_id,
            code=code,
            name=name,
            type=lt,
            parent_id=parent_id,
        )
        return self._repo.create_location(loc)  # type: ignore[no-any-return]

    def list_locations(self, company_id: UUID) -> list[Location]:
        return self._repo.list_locations(company_id)  # type: ignore[no-any-return]

    def get_location(self, lid: UUID) -> Location | None:
        return self._repo.get_location(lid)  # type: ignore[no-any-return]

    def get_category(self, cid: UUID) -> Any | None:
        return self._repo.get_category(cid)

    def post_opening_move(
        self,
        *,
        company_id: UUID,
        product_id: UUID,
        location_id: UUID,
        qty: Any,
        unit_cost: Any,
        effective_date: Any,
        lot_id: UUID | None = None,
        actor: UUID,
        reason: str,
    ) -> StockMove:
        """Opening stock receipt: DONE move, no FY gate, no GL (opening GL covers)."""
        from src.bricks.inventory.domain import GENESIS_CHECKSUM, MoveState

        prod = self._repo.get_product(product_id)
        if prod is None or prod.company_id != company_id:
            raise ValueError(f"product {product_id} not found in company")
        loc = self._repo.get_location(location_id)
        if loc is None or loc.company_id != company_id:
            raise ValueError(f"location {location_id} not found in company")
        mv = StockMove(
            company_id=company_id,
            product_id=product_id,
            qty=_d(qty),
            unit_cost=_d(unit_cost),
            from_loc=None,
            to_loc=location_id,
            lot_id=lot_id,
            effective_date=effective_date,
            state=MoveState.DONE,
        )
        mv.checksum = mv.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        return self._repo.create_move(mv)  # type: ignore[no-any-return]

    # ── category ──
    def create_category(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        parent_id: UUID | None = None,
        cost_method: str | None = None,
        account_code: str | None = None,
        tax_category: str | None = None,
        actor: UUID,
        reason: str,
    ) -> Any:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        from src.bricks.inventory.domain import CostMethod, ProductCategory

        cm = CostMethod(cost_method) if cost_method else None
        cat = ProductCategory(
            company_id=company_id,
            code=code,
            name=name,
            parent_id=parent_id,
            cost_method=cm,
            account_code=account_code,
            tax_category=tax_category,
        )
        saved = self._repo.create_category(cat)
        if self._audit:
            self._audit.append(
                entity_type="inventory_category",
                entity_id=cat.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved

    def list_categories(self, company_id: UUID) -> list[Any]:
        return self._repo.list_categories(company_id)  # type: ignore[no-any-return]

    # ── warehouse ──
    def create_warehouse(
        self,
        *,
        company_id: UUID,
        code: str,
        name: str,
        address: str | None = None,
        manager_id: UUID | None = None,
        account_code: str | None = None,
        actor: UUID,
        reason: str,
    ) -> Any:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        from src.bricks.inventory.domain import Warehouse

        wh = Warehouse(
            company_id=company_id,
            code=code,
            name=name,
            address=address,
            manager_id=manager_id,
            account_code=account_code,
        )
        saved = self._repo.create_warehouse(wh)
        if self._audit:
            self._audit.append(
                entity_type="warehouse",
                entity_id=wh.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"code": code},
            )
        return saved

    def list_warehouses(self, company_id: UUID) -> list[Any]:
        return self._repo.list_warehouses(company_id)  # type: ignore[no-any-return]

    # ── lot ──
    def create_lot(
        self,
        *,
        company_id: UUID,
        product_id: UUID,
        lot_code: str,
        expiry_date: date | None = None,
        qty: Any = Decimal(0),
        actor: UUID,
        reason: str,
    ) -> Any:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        from src.bricks.inventory.domain import Lot

        lot = Lot(
            company_id=company_id,
            product_id=product_id,
            lot_code=lot_code,
            expiry_date=expiry_date,
            qty=_d(qty),
        )
        saved = self._repo.create_lot(lot)
        if self._audit:
            self._audit.append(
                entity_type="lot",
                entity_id=lot.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"lot_code": lot_code},
            )
        return saved

    def list_lots(self, company_id: UUID, product_id: UUID | None = None) -> list[Any]:
        return self._repo.list_lots(company_id, product_id)  # type: ignore[no-any-return]

    # ── price list ──
    def create_price(
        self,
        *,
        company_id: UUID,
        product_id: UUID,
        uom_id: UUID | None = None,
        price: Any = Decimal(0),
        valid_from: date | None = None,
        actor: UUID,
        reason: str,
    ) -> Any:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        from src.bricks.inventory.domain import PriceList

        pl = PriceList(
            company_id=company_id,
            product_id=product_id,
            uom_id=uom_id,
            price=_d(price),
            valid_from=valid_from or date.today(),  # noqa: DTZ011
        )
        saved = self._repo.create_price(pl)
        if self._audit:
            self._audit.append(
                entity_type="price_list",
                entity_id=pl.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"price": str(price)},
            )
        return saved

    def list_prices(self, company_id: UUID, product_id: UUID | None = None) -> list[Any]:
        return self._repo.list_prices(company_id, product_id)  # type: ignore[no-any-return]

    # ── shipment ──
    def create_shipment(
        self,
        *,
        company_id: UUID,
        type: str,
        moves: list[dict[str, Any]],
        effective_date: date | None = None,
        actor: UUID,
        reason: str,
    ) -> Shipment:
        if not actor or not reason.strip():
            raise ValueError("actor and reason required")
        if not moves:
            raise ValueError("moves required")
        ed = effective_date or date.today()  # noqa: DTZ011
        # FY gate
        if self._fy.find_open_period(company_id, ed) is None:
            raise NoOpenPeriodError("Kỳ sổ chưa mở cho ngày hạch toán")
        if self._repo.is_period_closed(company_id, ed.year, ed.month):
            raise PeriodClosedError("Kỳ kho đã khóa")
        try:
            st = ShipmentType(type)
        except ValueError:
            raise ValueError(f"shipment type {type} invalid")
        # validate each move product/loc
        for m in moves:
            pid = UUID(str(m["product_id"]))
            prod = self._repo.get_product(pid)
            if not prod or prod.company_id != company_id:
                raise NotFoundError(f"product {m['product_id']} not found")
            if not prod.active:
                raise ValueError(f"product {prod.code} inactive")
            if _d(m["qty"]) <= 0:
                raise ValueError("qty must be >0")
            if _d(m.get("unit_cost", "0")) < 0:
                raise ValueError("unit_cost must be >=0")
            # cost method standard requires standard_cost
            if prod.cost_method == CostMethod.STANDARD and prod.standard_cost is None:
                raise ValueError(f"standard_cost required for {prod.code}")
        number = self._numbering.issue(company_id, st)
        ship = Shipment(
            company_id=company_id,
            type=st,
            number=number,
            effective_date=ed,
            moves=[],
            state=ShipState.DRAFT,
        )
        ship.checksum = ship.compute_checksum(GENESIS_CHECKSUM, actor, reason)
        saved_ship = self._repo.create_shipment(ship)
        # create moves as DRAFT linked to shipment
        move_ids: list[UUID] = []
        for m in moves:
            pid = UUID(str(m["product_id"]))
            qty = _d(m["qty"])
            unit_cost = _d(m.get("unit_cost", "0"))
            from_loc = UUID(str(m["from_loc"])) if m.get("from_loc") else None
            to_loc = UUID(str(m["to_loc"])) if m.get("to_loc") else None
            lot_id = UUID(str(m["lot_id"])) if m.get("lot_id") else None
            # for SUPPLIER_IN, to_loc required; CUSTOMER_OUT from_loc required; INTERNAL both
            if st == ShipmentType.SUPPLIER_IN and to_loc is None:
                raise ValueError("to_loc required for SUPPLIER_IN")
            if st == ShipmentType.CUSTOMER_OUT and from_loc is None:
                raise ValueError("from_loc required for CUSTOMER_OUT")
            if st == ShipmentType.INTERNAL and (from_loc is None or to_loc is None):
                raise ValueError("both locations required for INTERNAL")
            mv = StockMove(
                company_id=company_id,
                product_id=pid,
                qty=qty,
                unit_cost=unit_cost,
                from_loc=from_loc,
                to_loc=to_loc,
                lot_id=lot_id,
                effective_date=ed,
                shipment_id=saved_ship.id,
                state=self._import_move_state("DRAFT"),
            )
            mv.checksum = mv.compute_checksum(GENESIS_CHECKSUM, actor, reason)
            saved_mv = self._repo.create_move(mv)
            move_ids.append(saved_mv.id)
        saved_ship.moves = move_ids
        self._repo.update_shipment(saved_ship)
        if self._audit:
            self._audit.append(
                entity_type="inventory_shipment",
                entity_id=saved_ship.id,
                action="CREATE",
                actor_id=actor,
                reason=reason,
                after_value={"number": number, "type": type},
            )
        return saved_ship  # type: ignore[no-any-return]

    def post_shipment(self, shipment_id: UUID, *, actor: UUID, reason: str) -> Shipment:
        ship = self._repo.get_shipment(shipment_id)
        if not ship:
            raise NotFoundError("shipment not found")
        if ship.state == ShipState.DONE:
            raise ValueError("shipment already DONE")
        # FY + period re-check
        if self._fy.find_open_period(ship.company_id, ship.effective_date) is None:
            raise NoOpenPeriodError("Kỳ sổ chưa mở")
        if self._repo.is_period_closed(
            ship.company_id, ship.effective_date.year, ship.effective_date.month
        ):
            raise PeriodClosedError("Kỳ kho đã khóa")
        # for CUSTOMER_OUT, check stock sufficiency and compute COGS per method
        total_cogs = Decimal(0)
        total_variance = Decimal(0)
        for mid in ship.moves:
            mv = self._repo.get_move(mid)
            if not mv:
                continue
            prod = self._repo.get_product(mv.product_id)
            if not prod:
                continue
            if ship.type == ShipmentType.CUSTOMER_OUT:
                # stock check at from_loc
                available = self._repo.get_stock_qty(ship.company_id, mv.product_id, mv.from_loc)
                if available < mv.qty:
                    raise InsufficientStockError(
                        f"Tồn kho không đủ: need {mv.qty} have {available} for {prod.code}"
                    )
                # compute cost per method
                if prod.cost_method == CostMethod.STANDARD:
                    assert prod.standard_cost is not None
                    actual = moving_average_unit(
                        self._repo.get_stock_qty(prod.company_id, prod.id),
                        self._repo.get_stock_value(prod.company_id, prod.id),
                        mv.unit_cost or Decimal(0),
                    )
                    cogs_line, var_line = split_standard(actual, prod.standard_cost, mv.qty)
                    total_cogs += cogs_line
                    total_variance += var_line
                    mv.unit_cost = prod.standard_cost  # stock stays at standard
                else:
                    cogs_unit = self._compute_out_cost(prod, mv)
                    total_cogs += cogs_unit * mv.qty
                    mv.unit_cost = cogs_unit  # store actual COGS unit for value tracking
            # internal or supplier: unit_cost already set
            mv.state = self._import_move_state("DONE")
            mv.checksum = mv.compute_checksum(mv.checksum or GENESIS_CHECKSUM, actor, reason)
            self._repo.update_move(mv)
        ship.state = ShipState.DONE
        ship.checksum = ship.compute_checksum(ship.checksum or GENESIS_CHECKSUM, actor, reason)
        self._repo.update_shipment(ship)
        # GL posting for 152/632 via voucher if available and not internal
        if self._voucher and ship.type != ShipmentType.INTERNAL:
            try:
                regime = self._regime_of(ship.company_id) if self._regime_of else "tt133"
                # resolve accounts per regime (TT99 vs TT133 same 152/632)
                from src.bricks.coa.domain import resolve_chart_role

                # fallback to direct codes if resolve fails
                try:
                    inv_acc = resolve_chart_role("inventory", regime)  # 152
                except Exception:  # noqa: BLE001
                    inv_acc = "1521"
                try:
                    cogs_acc = resolve_chart_role("cogs", regime)
                except Exception:  # noqa: BLE001
                    cogs_acc = "6321"
                try:
                    sup_acc = resolve_chart_role("ap", regime)
                except Exception:  # noqa: BLE001
                    sup_acc = "3311"
            except Exception:  # noqa: BLE001
                inv_acc, cogs_acc, sup_acc = "1521", "6321", "3311"
            variance_acc = None
            if self._variance_account_of is not None:
                variance_acc = self._variance_account_of(ship.company_id) or None
            if ship.type == ShipmentType.SUPPLIER_IN:
                total_val = sum(
                    self._repo.get_move(mid).qty * self._repo.get_move(mid).unit_cost
                    for mid in ship.moves
                )
                if total_val > 0:
                    self._voucher.create_voucher(
                        company_id=ship.company_id,
                        entry_date=ship.effective_date,
                        description=f"Nhập kho {ship.number}",
                        lines=[
                            {"account_code": inv_acc, "debit": str(total_val), "credit": "0"},
                            {"account_code": sup_acc, "debit": "0", "credit": str(total_val)},
                        ],
                        actor=actor,
                        reason=reason,
                    )
            elif ship.type == ShipmentType.CUSTOMER_OUT and total_cogs > 0:
                # Variance has its own line when a panel account is set and
                # differs from COGS; otherwise it rides the COGS line (legacy).
                lines = [
                    {"account_code": cogs_acc, "debit": str(total_cogs), "credit": "0"},
                    {"account_code": inv_acc, "debit": "0", "credit": str(total_cogs)},
                ]
                if total_variance != 0 and variance_acc and variance_acc != cogs_acc:
                    if total_variance > 0:
                        lines.append(
                            {
                                "account_code": variance_acc,
                                "debit": str(total_variance),
                                "credit": "0",
                            }
                        )
                        lines.append(
                            {
                                "account_code": inv_acc,
                                "debit": "0",
                                "credit": str(total_variance),
                            }
                        )
                    else:
                        lines.append(
                            {
                                "account_code": inv_acc,
                                "debit": str(-total_variance),
                                "credit": "0",
                            }
                        )
                        lines.append(
                            {
                                "account_code": variance_acc,
                                "debit": "0",
                                "credit": str(-total_variance),
                            }
                        )
                else:
                    # legacy: variance rides COGS line (audit carries the split)
                    lines[0]["debit"] = str(total_cogs + total_variance)
                    lines[1]["credit"] = str(total_cogs + total_variance)
                self._voucher.create_voucher(
                    company_id=ship.company_id,
                    entry_date=ship.effective_date,
                    description=f"Giá vốn {ship.number}",
                    lines=lines,
                    actor=actor,
                    reason=reason,
                )
        if self._audit:
            self._audit.append(
                entity_type="inventory_shipment",
                entity_id=ship.id,
                action="POST",
                actor_id=actor,
                reason=reason,
                after_value={
                    "state": "DONE",
                    "cogs_total": float(total_cogs),
                    "variance_total": float(total_variance),
                },
            )
        return ship  # type: ignore[no-any-return]

    def _compute_out_cost(self, prod: Product, move: StockMove) -> Decimal:
        """Return unit COGS per product cost method. Math lives in costing.py."""
        if prod.cost_method == CostMethod.STANDARD:
            assert prod.standard_cost is not None
            return prod.standard_cost
        if prod.cost_method == CostMethod.SPECIFIC:
            return specific_out_unit(move.unit_cost, prod.standard_cost)
        if prod.cost_method == CostMethod.WAVG:
            return moving_average_unit(
                self._repo.get_stock_qty(prod.company_id, prod.id),
                self._repo.get_stock_value(prod.company_id, prod.id),
                move.unit_cost or Decimal(0),
            )
        if prod.cost_method == CostMethod.FIFO:
            moves = self._repo.list_moves(prod.company_id, product_id=prod.id, state="DONE")
            ins, outs = fifo_lots_from_moves(moves)
            unit = fifo_out_unit(ins, outs)
            if unit > 0:
                return unit
            # fallback to last receipt cost or move cost
            receipts = [m for m in moves if m.from_loc is None]
            if receipts:
                return receipts[-1].unit_cost  # type: ignore[no-any-return]
            return move.unit_cost or Decimal(0)
        return move.unit_cost

    def get_stock(
        self,
        company_id: UUID,
        product_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        as_of: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        # if product_id None list all products
        prods: list[Product | None] = (
            [self._repo.get_product(product_id)]
            if product_id
            else self._repo.list_products(company_id)
        )
        page = max(1, int(page))
        page_size = min(200, max(1, int(page_size)))
        out = []
        for p in prods[(page - 1) * page_size : page * page_size]:
            if not p:
                continue
            qty = self._repo.get_stock_qty(company_id, p.id, warehouse_id)
            val = self._repo.get_stock_value(company_id, p.id)
            out.append(
                {
                    "product_id": str(p.id),
                    "code": p.code,
                    "name": p.name,
                    "uom": p.uom,
                    "cost_method": p.cost_method.value,
                    "qty": float(qty),
                    "value": float(val),
                }
            )
        return out

    def nxt_report(self, company_id: UUID, from_date: date, to_date: date) -> list[dict[str, Any]]:
        prods = self._repo.list_products(company_id)
        rows = []
        for p in prods:
            moves = self._repo.list_moves(
                company_id, product_id=p.id, from_date=from_date, to_date=to_date, state="DONE"
            )
            in_qty = sum(m.qty for m in moves if m.from_loc is None)
            in_val = sum(m.qty * m.unit_cost for m in moves if m.from_loc is None)
            out_qty = sum(m.qty for m in moves if m.to_loc is None)
            out_val = sum(m.qty * m.unit_cost for m in moves if m.to_loc is None)
            begin_qty = self._repo.get_stock_qty(company_id, p.id) - in_qty + out_qty
            # approximate begin value via get value before period (simplify)
            rows.append(
                {
                    "product_id": str(p.id),
                    "code": p.code,
                    "begin_qty": float(begin_qty),
                    "in_qty": float(in_qty),
                    "in_value": float(in_val),
                    "out_qty": float(out_qty),
                    "out_value": float(out_val),
                    "end_qty": float(self._repo.get_stock_qty(company_id, p.id)),
                    "end_value": float(self._repo.get_stock_value(company_id, p.id)),
                }
            )
        return rows

    def turnover(self, company_id: UUID, from_date: date, to_date: date) -> list[dict[str, Any]]:
        rows = self.nxt_report(company_id, from_date, to_date)
        for r in rows:
            avg = (r["begin_qty"] + r["end_qty"]) / 2 if (r["begin_qty"] + r["end_qty"]) != 0 else 0
            r["turnover"] = r["out_qty"] / avg if avg else 0
        return rows

    def close_period(
        self, company_id: UUID, year: int, month: int, actor: UUID, reason: str
    ) -> None:
        if not 1 <= month <= 12:
            raise ValueError("month 1-12")
        self._repo.close_period(company_id, year, month)
        if self._audit:
            self._audit.append(
                entity_type="inventory_period",
                entity_id=uuid4(),
                action="CLOSE",
                actor_id=actor,
                reason=reason,
                after_value={"year": year, "month": month},
            )

    def count_inventory(
        self,
        company_id: UUID,
        location_id: UUID,
        counts: list[dict[str, Any]],
        actor: UUID,
        reason: str,
    ) -> Shipment:
        loc = self._repo.get_location(location_id)
        if not loc or loc.company_id != company_id:
            raise NotFoundError("location not found")
        # build adjustment shipment
        moves: list[dict[str, Any]] = []
        for c in counts:
            pid = UUID(str(c["product_id"]))
            prod = self._repo.get_product(pid)
            if not prod:
                raise NotFoundError(f"product {c['product_id']}")
            counted = _d(c["qty"])
            expected = self._repo.get_stock_qty(company_id, pid, location_id)
            diff = counted - expected
            if diff == 0:
                continue
            if diff > 0:
                # surplus → in from virtual
                moves.append(
                    {
                        "product_id": str(pid),
                        "qty": str(diff),
                        "unit_cost": str(prod.standard_cost or "0"),
                        "from_loc": None,
                        "to_loc": str(location_id),
                    }
                )
            else:
                moves.append(
                    {
                        "product_id": str(pid),
                        "qty": str(-diff),
                        "unit_cost": str(self._get_current_cost(prod)),
                        "from_loc": str(location_id),
                        "to_loc": None,
                    }
                )
        if not moves:
            raise ValueError("no difference to adjust")
        # effective today
        ship = self.create_shipment(
            company_id=company_id, type="internal", moves=moves, actor=actor, reason=reason
        )
        # but need to differentiate virtual? use internal with from/to virtual translation: supplier/customer not ideal
        # force type internal then post will handle; for surplus we treat as supplier_in cost
        # simplify: just post as is with current logic (internal no GL)
        # so for inventory count adjustments we need GL: surplus 152 debit, shortage 632
        # we handle by posting manually via voucher in post? skip for MVP
        return self.post_shipment(ship.id, actor=actor, reason=reason)

    def _get_current_cost(self, prod: Product) -> Decimal:
        if prod.cost_method == CostMethod.STANDARD and prod.standard_cost:
            return prod.standard_cost
        # fallback to last in cost or average
        moves = self._repo.list_moves(prod.company_id, product_id=prod.id, state="DONE")
        ins = [m for m in moves if m.from_loc is None]
        if ins:
            return ins[-1].unit_cost  # type: ignore[no-any-return]
        return Decimal(0)

    @staticmethod
    def _import_move_state(v: str) -> Any:
        from src.bricks.inventory.domain import MoveState

        return MoveState(v)
