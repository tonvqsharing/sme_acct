"""TDD RED — Slice5: costing engine + Standard variance booking."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.bricks.inventory.costing import (
    fifo_out_unit,
    moving_average_unit,
    specific_out_unit,
    split_standard,
)
from src.bricks.inventory.services import InventoryService

COMPANY = uuid4()


def test_moving_average_unit():
    assert moving_average_unit(Decimal(100), Decimal(1000000), Decimal(0)) == Decimal(10000)
    assert moving_average_unit(Decimal(0), Decimal(0), Decimal(7000)) == Decimal(7000)


def test_specific_out_unit_fallback():
    assert specific_out_unit(Decimal(0), Decimal(500000)) == Decimal(500000)
    assert specific_out_unit(Decimal(12000), Decimal(500000)) == Decimal(12000)


def test_fifo_out_unit_picks_oldest():
    lots = [(Decimal(50), Decimal(10000)), (Decimal(50), Decimal(12000))]
    assert fifo_out_unit(lots, []) == Decimal(10000)


def test_split_standard_positive_variance():
    cogs, variance = split_standard(Decimal(520000), Decimal(500000), Decimal(2))
    assert cogs == Decimal(1000000)
    assert variance == Decimal(40000)


def test_split_standard_negative_variance():
    cogs, variance = split_standard(Decimal(480000), Decimal(500000), Decimal(2))
    assert cogs == Decimal(1000000)
    assert variance == Decimal(-40000)


class FakeFY:
    def find_open_period(self, cid, d):
        return type("P", (), {"sequence": 1})


class FakeNumbering:
    def issue(self, cid, ship_type=None):
        return "PX/000001"


class FakeVoucher:
    def __init__(self):
        self.lines = None

    def create_voucher(self, **kw):
        self.lines = kw["lines"]
        return type("V", (), {"id": uuid4()})()


class FakeAudit:
    def __init__(self):
        self.entries: list = []

    def append(self, **kw):
        self.entries.append(kw)


class FakeRepo:
    def __init__(self):
        self.products: dict = {}
        self.moves: dict = {}
        self.shipments: dict = {}

    def get_product_by_code(self, cid, code):
        return None

    def create_product(self, p):
        self.products[p.id] = p
        return p

    def get_product(self, pid):
        return self.products.get(pid)

    def create_move(self, m):
        self.moves[m.id] = m
        return m

    def get_move(self, mid):
        return self.moves.get(mid)

    def update_move(self, m):
        self.moves[m.id] = m
        return m

    def list_moves(
        self, cid, product_id=None, location_id=None, from_date=None, to_date=None, state=None
    ):
        lst = [m for m in self.moves.values() if m.company_id == cid]
        if product_id:
            lst = [m for m in lst if m.product_id == product_id]
        if state:
            lst = [m for m in lst if m.state.value == state]
        return lst

    def create_shipment(self, s):
        self.shipments[s.id] = s
        return s

    def get_shipment(self, sid):
        return self.shipments.get(sid)

    def update_shipment(self, s):
        self.shipments[s.id] = s
        return s

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
        val = Decimal(0)
        for m in self.moves.values():
            if m.company_id != cid or m.product_id != pid or m.state.value != "DONE":
                continue
            if m.from_loc is None:
                val += m.qty * m.unit_cost
            elif m.to_loc is None:
                val -= m.qty * m.unit_cost
        return val

    def is_period_closed(self, cid, year, month):
        return False

    def get_category(self, cid):
        return None


def test_standard_out_books_variance_into_cogs_line():
    repo = FakeRepo()
    voucher = FakeVoucher()
    audit = FakeAudit()
    svc = InventoryService(
        repo=repo, fy=FakeFY(), numbering=FakeNumbering(), audit=audit, voucher_service=voucher
    )
    prod = svc.create_product(
        company_id=COMPANY,
        code="SKU-S",
        name="Bàn",
        uom="Cái",
        cost_method="standard",
        standard_cost="500000",
        actor=uuid4(),
        reason="p",
    )
    loc_id = uuid4()
    ship_in = svc.create_shipment(
        company_id=COMPANY,
        type="supplier_in",
        moves=[
            {"product_id": str(prod.id), "qty": "10", "unit_cost": "520000", "to_loc": str(loc_id)}
        ],
        actor=uuid4(),
        reason="in",
    )
    svc.post_shipment(ship_in.id, actor=uuid4(), reason="p")
    ship_out = svc.create_shipment(
        company_id=COMPANY,
        type="customer_out",
        moves=[{"product_id": str(prod.id), "qty": "2", "from_loc": str(loc_id)}],
        actor=uuid4(),
        reason="out",
    )
    svc.post_shipment(ship_out.id, actor=uuid4(), reason="p")
    # standard 500k x 2 = 1M COGS + 40k variance booked into same 6321 line (no variance account yet)
    debit = Decimal(voucher.lines[0]["debit"])
    assert debit == Decimal(1040000)
    post_entries = [e for e in audit.entries if e["action"] == "POST"]
    assert post_entries[-1]["after_value"]["variance_total"] == 40000.0
    assert post_entries[-1]["after_value"]["cogs_total"] == 1000000.0


def _setup_standard_stock(svc, code="SKU-V"):
    prod = svc.create_product(
        company_id=COMPANY,
        code=code,
        name="Bàn V",
        uom="Cái",
        cost_method="standard",
        standard_cost="500000",
        actor=uuid4(),
        reason="p",
    )
    loc_id = uuid4()
    ship_in = svc.create_shipment(
        company_id=COMPANY,
        type="supplier_in",
        moves=[
            {"product_id": str(prod.id), "qty": "10", "unit_cost": "520000", "to_loc": str(loc_id)}
        ],
        actor=uuid4(),
        reason="in",
    )
    svc.post_shipment(ship_in.id, actor=uuid4(), reason="p")
    return prod, loc_id


def test_variance_account_gets_own_balanced_lines():
    repo = FakeRepo()
    voucher = FakeVoucher()
    svc = InventoryService(
        repo=repo,
        fy=FakeFY(),
        numbering=FakeNumbering(),
        audit=FakeAudit(),
        voucher_service=voucher,
        variance_account_of=lambda cid: "6328",
    )
    prod, loc_id = _setup_standard_stock(svc)
    ship_out = svc.create_shipment(
        company_id=COMPANY,
        type="customer_out",
        moves=[{"product_id": str(prod.id), "qty": "2", "from_loc": str(loc_id)}],
        actor=uuid4(),
        reason="out",
    )
    svc.post_shipment(ship_out.id, actor=uuid4(), reason="p")
    posted = [(ln["account_code"], ln["debit"], ln["credit"]) for ln in voucher.lines]
    # standard COGS + inventory relief at standard; variance on its own account
    assert ("6321", "1000000", "0") in posted
    assert ("1521", "0", "1000000") in posted
    assert ("6328", "40000", "0") in posted
    assert ("1521", "0", "40000") in posted
    total_debit = sum(Decimal(ln["debit"]) for ln in voucher.lines)
    total_credit = sum(Decimal(ln["credit"]) for ln in voucher.lines)
    assert total_debit == total_credit == Decimal(1040000)
