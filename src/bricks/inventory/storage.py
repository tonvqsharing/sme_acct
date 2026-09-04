"""Inventory storage — SQLAlchemy adapter. No 611, Tryton-like."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.inventory.domain import (
    CostMethod,
    Location,
    LocationType,
    Product,
    Shipment,
    ShipmentType,
    StockMove,
)


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "inventory_products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(200))
    uom: Mapped[str] = mapped_column(String(20))
    uom_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cost_method: Mapped[str] = mapped_column(String(20))
    standard_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    checksum: Mapped[str] = mapped_column(String(64), default="")


class LocationModel(Base):
    __tablename__ = "inventory_locations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    warehouse_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class StockMoveModel(Base):
    __tablename__ = "inventory_moves"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    from_loc: Mapped[str | None] = mapped_column(String(36), nullable=True)
    to_loc: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date)
    shipment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


class ShipmentModel(Base):
    __tablename__ = "inventory_shipments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(20))
    number: Mapped[str] = mapped_column(String(30), index=True)
    effective_date: Mapped[date] = mapped_column(Date)
    moves: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


class StockPeriodModel(Base):
    __tablename__ = "inventory_periods"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    year: Mapped[int] = mapped_column(String(10))  # store int as string for sqlite compat
    month: Mapped[int] = mapped_column(String(10))
    state: Mapped[str] = mapped_column(String(20), default="OPEN")


class CostRevisionModel(Base):
    __tablename__ = "inventory_cost_revisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    effective_date: Mapped[date] = mapped_column(Date)
    old_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    new_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    reason: Mapped[str] = mapped_column(String(200))


class ProductCategoryModel(Base):
    __tablename__ = "inventory_categories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cost_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    account_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tax_category: Mapped[str | None] = mapped_column(String(30), nullable=True)


class WarehouseModel(Base):
    __tablename__ = "inventory_warehouses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    account_code: Mapped[str | None] = mapped_column(String(10), nullable=True)


class LotModel(Base):
    __tablename__ = "inventory_lots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_code: Mapped[str] = mapped_column(String(30), index=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)


class PriceListModel(Base):
    __tablename__ = "inventory_price_lists"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    uom_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    valid_from: Mapped[date] = mapped_column(Date)


class SQLAlchemyInventoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ── products ──
    def create_product(self, p: Product) -> Product:
        self._session.add(
            ProductModel(
                id=str(p.id),
                company_id=str(p.company_id),
                code=p.code,
                name=p.name,
                uom=p.uom,
                uom_id=str(p.uom_id) if p.uom_id else None,
                category_id=str(p.category_id) if p.category_id else None,
                cost_method=p.cost_method.value,
                standard_cost=p.standard_cost,
                active=p.active,
                checksum=p.checksum,
            )
        )
        self._session.commit()
        return p

    def get_product(self, pid: UUID) -> Product | None:
        m = self._session.get(ProductModel, str(pid))
        return self._to_product(m) if m else None

    def get_product_by_code(self, company_id: UUID, code: str) -> Product | None:
        row = (
            self._session.query(ProductModel)
            .filter(ProductModel.company_id == str(company_id), ProductModel.code == code)
            .first()
        )
        return self._to_product(row) if row else None

    def list_products(self, company_id: UUID) -> list[Product]:
        rows = (
            self._session.query(ProductModel)
            .filter(ProductModel.company_id == str(company_id))
            .all()
        )
        return [self._to_product(r) for r in rows]

    @staticmethod
    def _to_product(m: ProductModel) -> Product:
        return Product(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            uom=m.uom,
            uom_id=UUID(m.uom_id) if m.uom_id else None,
            category_id=UUID(m.category_id) if m.category_id else None,
            cost_method=CostMethod(m.cost_method),
            standard_cost=Decimal(str(m.standard_cost)) if m.standard_cost is not None else None,
            active=m.active,
            checksum=m.checksum,
        )

    def update_product(self, p: Product) -> Product:
        m = self._session.get(ProductModel, str(p.id))
        if m is None:
            raise ValueError("not found")
        m.name = p.name
        m.uom = p.uom
        m.uom_id = str(p.uom_id) if p.uom_id else None
        m.category_id = str(p.category_id) if p.category_id else None
        m.cost_method = p.cost_method.value
        m.standard_cost = p.standard_cost
        m.active = p.active
        m.checksum = p.checksum
        self._session.commit()
        return p

    # ── locations ──
    def create_location(self, loc: Location) -> Location:
        self._session.add(
            LocationModel(
                id=str(loc.id),
                company_id=str(loc.company_id),
                warehouse_id=str(loc.warehouse_id) if loc.warehouse_id else None,
                code=loc.code,
                name=loc.name,
                type=loc.type.value,
                parent_id=str(loc.parent_id) if loc.parent_id else None,
            )
        )
        self._session.commit()
        return loc

    def get_location(self, lid: UUID) -> Location | None:
        m = self._session.get(LocationModel, str(lid))
        if not m:
            return None
        return Location(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            warehouse_id=UUID(m.warehouse_id) if m.warehouse_id else None,
            code=m.code,
            name=m.name,
            type=LocationType(m.type),
            parent_id=UUID(m.parent_id) if m.parent_id else None,
        )

    def list_locations(self, company_id: UUID) -> list[Location]:
        rows = (
            self._session.query(LocationModel)
            .filter(LocationModel.company_id == str(company_id))
            .all()
        )
        return [
            Location(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                warehouse_id=UUID(r.warehouse_id) if r.warehouse_id else None,
                code=r.code,
                name=r.name,
                type=LocationType(r.type),
                parent_id=UUID(r.parent_id) if r.parent_id else None,
            )
            for r in rows
        ]

    # ── shipments ──
    def create_shipment(self, s: Shipment) -> Shipment:
        self._session.add(
            ShipmentModel(
                id=str(s.id),
                company_id=str(s.company_id),
                type=s.type.value,
                number=s.number,
                effective_date=s.effective_date,
                moves=[str(x) for x in s.moves],
                state=s.state.value,
                checksum=s.checksum,
            )
        )
        self._session.commit()
        return s

    def get_shipment(self, sid: UUID) -> Shipment | None:
        m = self._session.get(ShipmentModel, str(sid))
        if not m:
            return None
        return Shipment(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            type=ShipmentType(m.type),
            number=m.number,
            effective_date=m.effective_date,
            moves=[UUID(x) for x in (m.moves or [])],
            state=__import__("src.bricks.inventory.domain", fromlist=["ShipState"]).ShipState(
                m.state
            ),
            checksum=m.checksum,
        )

    def update_shipment(self, s: Shipment) -> Shipment:
        m = self._session.get(ShipmentModel, str(s.id))
        if m is None:
            raise ValueError("not found")
        m.state = s.state.value
        m.moves = [str(x) for x in s.moves]
        m.checksum = s.checksum
        self._session.commit()
        return s

    # ── moves ──
    def create_move(self, m: StockMove) -> StockMove:
        self._session.add(
            StockMoveModel(
                id=str(m.id),
                company_id=str(m.company_id),
                product_id=str(m.product_id),
                qty=m.qty,
                unit_cost=m.unit_cost,
                from_loc=str(m.from_loc) if m.from_loc else None,
                to_loc=str(m.to_loc) if m.to_loc else None,
                lot_id=str(m.lot_id) if m.lot_id else None,
                effective_date=m.effective_date,
                shipment_id=str(m.shipment_id) if m.shipment_id else None,
                state=m.state.value,
                checksum=m.checksum,
            )
        )
        self._session.commit()
        return m

    def get_move(self, mid: UUID) -> StockMove | None:
        row = self._session.get(StockMoveModel, str(mid))
        if not row:
            return None
        return self._to_move(row)

    def list_moves(
        self,
        company_id: UUID,
        product_id: UUID | None = None,
        location_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        state: str | None = None,
    ) -> list[StockMove]:
        q = self._session.query(StockMoveModel).filter(StockMoveModel.company_id == str(company_id))
        if product_id:
            q = q.filter(StockMoveModel.product_id == str(product_id))
        if state:
            q = q.filter(StockMoveModel.state == state)
        if from_date:
            q = q.filter(StockMoveModel.effective_date >= from_date)
        if to_date:
            q = q.filter(StockMoveModel.effective_date <= to_date)
        rows = q.order_by(StockMoveModel.effective_date.asc()).all()
        moves = [self._to_move(r) for r in rows]
        if location_id:
            # filter where location participates (from or to)
            lid = str(location_id)
            moves = [m for m in moves if str(m.from_loc) == lid or str(m.to_loc) == lid]
        return moves

    def update_move(self, m: StockMove) -> StockMove:
        row = self._session.get(StockMoveModel, str(m.id))
        if row is None:
            raise ValueError("not found")
        row.state = m.state.value
        row.checksum = m.checksum
        self._session.commit()
        return m

    @staticmethod
    def _to_move(r: StockMoveModel) -> StockMove:
        from src.bricks.inventory.domain import MoveState

        return StockMove(
            id=UUID(r.id),
            company_id=UUID(r.company_id),
            product_id=UUID(r.product_id),
            qty=Decimal(str(r.qty)),
            unit_cost=Decimal(str(r.unit_cost)),
            from_loc=UUID(r.from_loc) if r.from_loc else None,
            to_loc=UUID(r.to_loc) if r.to_loc else None,
            lot_id=UUID(r.lot_id) if r.lot_id else None,
            effective_date=r.effective_date,
            shipment_id=UUID(r.shipment_id) if r.shipment_id else None,
            state=MoveState(r.state),
            checksum=r.checksum,
        )

    def get_stock_qty(
        self, company_id: UUID, product_id: UUID, location_id: UUID | None = None
    ) -> Decimal:
        moves = self.list_moves(company_id, product_id=product_id, state="DONE")
        qty = Decimal(0)
        for m in moves:
            if location_id is not None:
                if m.to_loc == location_id:
                    qty += m.qty
                elif m.from_loc == location_id:
                    qty -= m.qty
            else:
                if m.from_loc is None and m.to_loc is not None:
                    qty += m.qty
                elif m.to_loc is None and m.from_loc is not None:
                    qty -= m.qty
                # internal net 0 for company
        return qty

    def get_stock_value(self, company_id: UUID, product_id: UUID) -> Decimal:
        # value = qty * current wavg or standard; for simplicity sum cost of DONE moves
        moves = self.list_moves(company_id, product_id=product_id, state="DONE")
        # moving wavg value: compute iteratively
        qty = Decimal(0)
        value = Decimal(0)
        for m in moves:
            if m.from_loc is None:  # in
                qty += m.qty
                value += m.qty * m.unit_cost
            elif m.to_loc is None:  # out: need cost at time (stored unit_cost)
                qty -= m.qty
                value -= m.qty * m.unit_cost
            else:  # internal no value change
                pass
        return value if value >= 0 else Decimal(0)

    # period
    def is_period_closed(self, company_id: UUID, year: int, month: int) -> bool:
        row = (
            self._session.query(StockPeriodModel)
            .filter(
                StockPeriodModel.company_id == str(company_id),
                StockPeriodModel.year == str(year),
                StockPeriodModel.month == str(month),
            )
            .first()
        )
        return row is not None and row.state == "CLOSED"

    def close_period(self, company_id: UUID, year: int, month: int) -> None:
        row = (
            self._session.query(StockPeriodModel)
            .filter(
                StockPeriodModel.company_id == str(company_id),
                StockPeriodModel.year == str(year),
                StockPeriodModel.month == str(month),
            )
            .first()
        )
        if row:
            row.state = "CLOSED"
        else:
            self._session.add(
                StockPeriodModel(
                    id=str(__import__("uuid").uuid4()),
                    company_id=str(company_id),
                    year=str(year),
                    month=str(month),
                    state="CLOSED",
                )
            )
        self._session.commit()

    # ── category & warehouse ──
    def create_category(self, cat: Any) -> Any:
        self._session.add(
            ProductCategoryModel(
                id=str(cat.id),
                company_id=str(cat.company_id),
                code=cat.code,
                name=cat.name,
                parent_id=str(cat.parent_id) if cat.parent_id else None,
                cost_method=cat.cost_method.value if cat.cost_method else None,
                account_code=cat.account_code,
                tax_category=cat.tax_category,
            )
        )
        self._session.commit()
        return cat

    def list_categories(self, company_id: UUID) -> list[Any]:
        rows = (
            self._session.query(ProductCategoryModel)
            .filter(ProductCategoryModel.company_id == str(company_id))
            .all()
        )
        from src.bricks.inventory.domain import CostMethod, ProductCategory

        return [
            ProductCategory(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                code=r.code,
                name=r.name,
                parent_id=UUID(r.parent_id) if r.parent_id else None,
                cost_method=CostMethod(r.cost_method) if r.cost_method else None,
                account_code=r.account_code,
                tax_category=r.tax_category,
            )
            for r in rows
        ]

    def get_category(self, cid: UUID) -> Any | None:
        m = self._session.get(ProductCategoryModel, str(cid))
        if not m:
            return None
        from src.bricks.inventory.domain import CostMethod, ProductCategory

        return ProductCategory(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            parent_id=UUID(m.parent_id) if m.parent_id else None,
            cost_method=CostMethod(m.cost_method) if m.cost_method else None,
            account_code=m.account_code,
            tax_category=m.tax_category,
        )

    def create_warehouse(self, wh: Any) -> Any:
        self._session.add(
            WarehouseModel(
                id=str(wh.id),
                company_id=str(wh.company_id),
                code=wh.code,
                name=wh.name,
                address=wh.address,
                manager_id=str(wh.manager_id) if wh.manager_id else None,
                account_code=wh.account_code,
            )
        )
        self._session.commit()
        return wh

    def list_warehouses(self, company_id: UUID) -> list[Any]:
        rows = (
            self._session.query(WarehouseModel)
            .filter(WarehouseModel.company_id == str(company_id))
            .all()
        )
        from src.bricks.inventory.domain import Warehouse

        return [
            Warehouse(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                code=r.code,
                name=r.name,
                address=r.address,
                manager_id=UUID(r.manager_id) if r.manager_id else None,
                account_code=r.account_code,
            )
            for r in rows
        ]

    def get_warehouse(self, wid: UUID) -> Any | None:
        m = self._session.get(WarehouseModel, str(wid))
        if not m:
            return None
        from src.bricks.inventory.domain import Warehouse

        return Warehouse(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            code=m.code,
            name=m.name,
            address=m.address,
            manager_id=UUID(m.manager_id) if m.manager_id else None,
            account_code=m.account_code,
        )

    # ── lots ──
    def create_lot(self, lot: Any) -> Any:
        self._session.add(
            LotModel(
                id=str(lot.id),
                company_id=str(lot.company_id),
                product_id=str(lot.product_id),
                lot_code=lot.lot_code,
                expiry_date=lot.expiry_date,
                qty=lot.qty,
            )
        )
        self._session.commit()
        return lot

    def list_lots(self, company_id: UUID, product_id: UUID | None = None) -> list[Any]:
        q = self._session.query(LotModel).filter(LotModel.company_id == str(company_id))
        if product_id:
            q = q.filter(LotModel.product_id == str(product_id))
        rows = q.all()
        from src.bricks.inventory.domain import Lot

        return [
            Lot(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                product_id=UUID(r.product_id),
                lot_code=r.lot_code,
                expiry_date=r.expiry_date,
                qty=Decimal(str(r.qty)),
            )
            for r in rows
        ]

    # ── price lists ──
    def create_price(self, pl: Any) -> Any:
        self._session.add(
            PriceListModel(
                id=str(pl.id),
                company_id=str(pl.company_id),
                product_id=str(pl.product_id),
                uom_id=str(pl.uom_id) if pl.uom_id else None,
                price=pl.price,
                valid_from=pl.valid_from,
            )
        )
        self._session.commit()
        return pl

    def list_prices(self, company_id: UUID, product_id: UUID | None = None) -> list[Any]:
        q = self._session.query(PriceListModel).filter(PriceListModel.company_id == str(company_id))
        if product_id:
            q = q.filter(PriceListModel.product_id == str(product_id))
        rows = q.all()
        from src.bricks.inventory.domain import PriceList

        return [
            PriceList(
                id=UUID(r.id),
                company_id=UUID(r.company_id),
                product_id=UUID(r.product_id),
                uom_id=UUID(r.uom_id) if r.uom_id else None,
                price=Decimal(str(r.price)),
                valid_from=r.valid_from,
            )
            for r in rows
        ]
