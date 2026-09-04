"""TDD — Inventory S1-S5: product/location/move/cost/period."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.inventory.services import (
    DuplicateProductCodeError,
    InsufficientStockError,
    InventoryService,
    PeriodClosedError,
)

COMPANY = uuid4()


class FakeFY:
    def __init__(self, open_on=True):
        self.open_on = open_on

    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1}) if self.open_on else None


class FakeNumbering:
    def __init__(self):
        self.seq = 1

    def issue(self, cid, ship_type=None):
        # ship_type is ShipmentType
        prefix = {"supplier_in": "PN/", "customer_out": "PX/", "internal": "CK/"}.get(
            ship_type.value if hasattr(ship_type, "value") else "PN/", "PN/"
        )
        n = f"{prefix}{self.seq:06d}"
        self.seq += 1
        return n


class FakeRepo:
    def __init__(self):
        self.products: dict = {}
        self.locations: dict = {}
        self.shipments: dict = {}
        self.moves: dict = {}
        self.period_closed = False

    def get_product_by_code(self, cid, code):
        for p in self.products.values():
            if p.company_id == cid and p.code == code:
                return p
        return None

    def create_product(self, p):
        self.products[p.id] = p
        return p

    def get_product(self, pid):
        return self.products.get(pid)

    def list_products(self, cid):
        return [p for p in self.products.values() if p.company_id == cid]

    def create_location(self, loc):
        self.locations[loc.id] = loc
        return loc

    def get_location(self, lid):
        return self.locations.get(lid)

    def list_locations(self, cid):
        return [l for l in self.locations.values() if l.company_id == cid]

    def create_shipment(self, s):
        self.shipments[s.id] = s
        return s

    def get_shipment(self, sid):
        return self.shipments.get(sid)

    def update_shipment(self, s):
        self.shipments[s.id] = s
        return s

    def create_move(self, m):
        self.moves[m.id] = m
        return m

    def get_move(self, mid):
        return self.moves.get(mid)

    def list_moves(
        self, cid, product_id=None, location_id=None, from_date=None, to_date=None, state=None
    ):
        lst = [m for m in self.moves.values() if m.company_id == cid]
        if product_id:
            lst = [m for m in lst if m.product_id == product_id]
        if state:
            lst = [m for m in lst if m.state.value == state]
        return lst

    def update_move(self, m):
        self.moves[m.id] = m
        return m

    def get_stock_qty(self, cid, pid, lid=None):
        qty = Decimal(0)
        for m in self.moves.values():
            if m.company_id != cid or m.product_id != pid or m.state.value != "DONE":
                continue
            if m.from_loc is None and m.to_loc is not None:
                qty += m.qty
            elif m.to_loc is None and m.from_loc is not None:
                qty -= m.qty
        return qty

    def get_stock_value(self, cid, pid):
        qty = Decimal(0)
        val = Decimal(0)
        for m in self.moves.values():
            if m.company_id != cid or m.product_id != pid or m.state.value != "DONE":
                continue
            if m.from_loc is None:
                qty += m.qty
                val += m.qty * m.unit_cost
            elif m.to_loc is None:
                qty -= m.qty
                val -= m.qty * m.unit_cost
        return val

    def is_period_closed(self, cid, year, month):
        return self.period_closed

    def close_period(self, cid, year, month):
        self.period_closed = True


def _svc(open_on=True):
    return InventoryService(
        repo=FakeRepo(), fy=FakeFY(open_on), numbering=FakeNumbering(), audit=None
    )


class TestProduct:
    def test_create_and_duplicate(self):
        svc = _svc()
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-001",
            name="Bút",
            uom="Cái",
            cost_method="wavg",
            actor=uuid4(),
            reason="init",
        )
        assert p.code == "SKU-001"
        with pytest.raises(DuplicateProductCodeError):
            svc.create_product(
                company_id=COMPANY,
                code="SKU-001",
                name="dup",
                uom="Cái",
                cost_method="fifo",
                actor=uuid4(),
                reason="dup",
            )

    def test_standard_requires_cost(self):
        svc = _svc()
        with pytest.raises(ValueError, match="standard_cost"):
            svc.create_product(
                company_id=COMPANY,
                code="SKU-STD",
                name="Bàn",
                uom="Cái",
                cost_method="standard",
                actor=uuid4(),
                reason="x",
            )


class TestShipment:
    def test_supplier_in_and_customer_out_wavg(self):
        svc = _svc()
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-W",
            name="Bút",
            uom="Cái",
            cost_method="wavg",
            actor=uuid4(),
            reason="p",
        )
        loc = svc.create_location(
            company_id=COMPANY, warehouse_id=None, code="A-01", name="Kệ A", type="shelf"
        )
        ship_in = svc.create_shipment(
            company_id=COMPANY,
            type="supplier_in",
            moves=[
                {"product_id": str(p.id), "qty": "100", "unit_cost": "10000", "to_loc": str(loc.id)}
            ],
            actor=uuid4(),
            reason="in",
        )
        assert ship_in.number.startswith("PN/")
        svc.post_shipment(ship_in.id, actor=uuid4(), reason="post in")
        assert svc.get_stock(COMPANY, p.id)[0]["qty"] == 100.0
        # out 30 should use wavg 10k
        ship_out = svc.create_shipment(
            company_id=COMPANY,
            type="customer_out",
            moves=[{"product_id": str(p.id), "qty": "30", "from_loc": str(loc.id)}],
            actor=uuid4(),
            reason="out",
        )
        svc.post_shipment(ship_out.id, actor=uuid4(), reason="post out")
        stock = svc.get_stock(COMPANY, p.id)[0]
        assert stock["qty"] == 70.0

    def test_fifo_picks_oldest(self):
        svc = _svc()
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-F",
            name="Vở",
            uom="Cái",
            cost_method="fifo",
            actor=uuid4(),
            reason="p",
        )
        loc = svc.create_location(
            company_id=COMPANY, warehouse_id=None, code="A-01", name="Kệ", type="shelf"
        )
        s1 = svc.create_shipment(
            company_id=COMPANY,
            type="supplier_in",
            moves=[
                {"product_id": str(p.id), "qty": "50", "unit_cost": "10000", "to_loc": str(loc.id)}
            ],
            actor=uuid4(),
            reason="in1",
        )
        svc.post_shipment(s1.id, actor=uuid4(), reason="p1")
        s2 = svc.create_shipment(
            company_id=COMPANY,
            type="supplier_in",
            moves=[
                {"product_id": str(p.id), "qty": "50", "unit_cost": "12000", "to_loc": str(loc.id)}
            ],
            actor=uuid4(),
            reason="in2",
        )
        svc.post_shipment(s2.id, actor=uuid4(), reason="p2")
        # out 60 should consume 50@10k +10@12k FIFO; next cost is 12k lot
        s3 = svc.create_shipment(
            company_id=COMPANY,
            type="customer_out",
            moves=[{"product_id": str(p.id), "qty": "60", "from_loc": str(loc.id)}],
            actor=uuid4(),
            reason="out",
        )
        svc.post_shipment(s3.id, actor=uuid4(), reason="p3")
        # check stock 40 left @12k
        assert svc.get_stock(COMPANY, p.id)[0]["qty"] == 40.0

    def test_standard_cost(self):
        svc = _svc()
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-S",
            name="Bàn",
            uom="Cái",
            cost_method="standard",
            standard_cost="500000",
            actor=uuid4(),
            reason="p",
        )
        loc = svc.create_location(
            company_id=COMPANY, warehouse_id=None, code="A-01", name="K", type="shelf"
        )
        s_in = svc.create_shipment(
            company_id=COMPANY,
            type="supplier_in",
            moves=[
                {"product_id": str(p.id), "qty": "10", "unit_cost": "520000", "to_loc": str(loc.id)}
            ],
            actor=uuid4(),
            reason="in",
        )
        svc.post_shipment(s_in.id, actor=uuid4(), reason="p")
        s_out = svc.create_shipment(
            company_id=COMPANY,
            type="customer_out",
            moves=[{"product_id": str(p.id), "qty": "2", "from_loc": str(loc.id)}],
            actor=uuid4(),
            reason="out",
        )
        svc.post_shipment(s_out.id, actor=uuid4(), reason="p")
        # standard cost 500k used, variance 20k not stocked but cost fixed
        assert svc.get_stock(COMPANY, p.id)[0]["qty"] == 8.0

    def test_oversell_blocked(self):
        svc = _svc()
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-O",
            name="Bút",
            uom="Cái",
            cost_method="wavg",
            actor=uuid4(),
            reason="p",
        )
        loc = svc.create_location(
            company_id=COMPANY, warehouse_id=None, code="A-01", name="K", type="shelf"
        )
        s_in = svc.create_shipment(
            company_id=COMPANY,
            type="supplier_in",
            moves=[
                {"product_id": str(p.id), "qty": "10", "unit_cost": "1000", "to_loc": str(loc.id)}
            ],
            actor=uuid4(),
            reason="in",
        )
        svc.post_shipment(s_in.id, actor=uuid4(), reason="p")
        s_out = svc.create_shipment(
            company_id=COMPANY,
            type="customer_out",
            moves=[{"product_id": str(p.id), "qty": "20", "from_loc": str(loc.id)}],
            actor=uuid4(),
            reason="out",
        )
        with pytest.raises(InsufficientStockError):
            svc.post_shipment(s_out.id, actor=uuid4(), reason="p")

    def test_period_closed_blocks(self):
        svc = _svc()
        svc._repo.period_closed = True
        p = svc.create_product(
            company_id=COMPANY,
            code="SKU-P",
            name="X",
            uom="Cái",
            cost_method="wavg",
            actor=uuid4(),
            reason="p",
        )
        with pytest.raises(PeriodClosedError):
            svc.create_shipment(
                company_id=COMPANY,
                type="supplier_in",
                moves=[
                    {
                        "product_id": str(p.id),
                        "qty": "1",
                        "unit_cost": "100",
                        "to_loc": str(uuid4()),
                    }
                ],
                actor=uuid4(),
                reason="x",
            )

    def test_per_product_method_mixed(self):
        svc = _svc()
        p1 = svc.create_product(
            company_id=COMPANY,
            code="SKU-A",
            name="A",
            uom="Cái",
            cost_method="wavg",
            actor=uuid4(),
            reason="p",
        )
        p2 = svc.create_product(
            company_id=COMPANY,
            code="SKU-B",
            name="B",
            uom="Cái",
            cost_method="fifo",
            actor=uuid4(),
            reason="p",
        )
        assert p1.cost_method.value == "wavg"
        assert p2.cost_method.value == "fifo"
