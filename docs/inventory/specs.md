# Specs — Inventory Bricks (HTK)

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-09-03 |
| Brick | `src/bricks/inventory/` → `domain.py` pure + `services.py` ports + `storage.py` SQLA + `web_adapter.py` Flask |

## 1. Domain model (target v1, Tryton 8.0 parity)

```python
@dataclass
class Product:
    id: UUID
    company_id: UUID
    code: str           # SKU, unique per company
    name: str
    uom: str            # Hộp/Cái/kg
    cost_method: CostMethod  # SPECIFIC|WAVG|FIFO|STANDARD (TT99 §13 + Standard)
    standard_cost: Decimal | None  # for STANDARD
    active: bool = True

class CostMethod(Enum):
    SPECIFIC = "specific"   # đích danh — VAS 02 §14
    WAVG = "wavg"           # bình quân gia quyền §15
    FIFO = "fifo"           # nhập trước xuất trước §16
    STANDARD = "standard"   # chuẩn TT99 new

@dataclass
class Location:
    id: UUID
    company_id: UUID
    warehouse: UUID         # parent warehouse id
    code: str
    name: str
    parent_id: UUID | None
    type: LocType           # WAREHOUSE|SHELF|VIRTUAL

@dataclass
class StockMove:
    id: UUID
    company_id: UUID
    product_id: UUID
    qty: Decimal            # + for in, - for out (or from→to)
    unit_cost: Decimal      # giá gốc tại move
    from_loc: UUID | None   # None = supplier (in)
    to_loc: UUID | None     # None = customer (out)
    effective_date: date
    shipment_id: UUID | None
    state: MoveState = DRAFT  # DRAFT|ASSIGNED|DONE|CANCELLED
    checksum: str = ""

@dataclass
class Shipment:
    id: UUID
    company_id: UUID
    type: ShipmentType  # SUPPLIER_IN|CUSTOMER_OUT|INTERNAL
    number: str         # e.g. PN/000001, PX/000001
    moves: list[UUID]
    state: ShipState = DRAFT

@dataclass
class StockPeriod:
    id: UUID
    company_id: UUID
    year: int
    month: int
    state: PeriodState = OPEN  # OPEN|CLOSED
```

### Cost price revision (Tryton Cost Price Revision pattern)

```python
@dataclass
class CostRevision:
    product_id: UUID
    effective_date: date
    old_cost: Decimal
    new_cost: Decimal
    reason: str
```

## 2. Service contracts (ports primitives only)

```python
class InventoryService:
    def create_product(..., code, name, uom, cost_method, standard_cost?, actor, reason) -> Product
    def create_location(..., warehouse, code, name, parent?) -> Location
    def create_shipment(..., type, moves:[{product_id, qty, unit_cost, from,to}], actor, reason) -> Shipment
    def post_shipment(shipment_id, actor, reason) -> Shipment  # DRAFT→DONE + moves DONE + ledger 152/156/632 + cost revision
    def recompute_cost(product_id, method?) -> Decimal
    def count_inventory(location_id, counts:[{product,qty}]) -> InventoryCount
```

Gates (order):
```
1. actor+reason required
2. FY open on effective_date
3. product active + location belongs to company
4. qty>0, unit_cost>=0
5. for STANDARD: standard_cost required; for others optional
6. shipment balanced? (no 611)
7. period OPEN
8. checksum sha256(prev|id|actor|state|qty|reason)
```

## 3. HTTP API (only Flask file)

```
POST   /api/v1/inventory/products               — create product
GET    /api/v1/inventory/products?company_id=
POST   /api/v1/inventory/locations
POST   /api/v1/inventory/shipments              — DRAFT (group moves)
POST   /api/v1/inventory/shipments/<id>/post    — DONE + 152/632 posting
GET    /api/v1/inventory/stock?company_id=&warehouse=&as_of=
GET    /api/v1/reports/inventory/nxt?company_id=&from=&to=
GET    /api/v1/reports/inventory/turnover?company_id=&warehouse=
POST   /api/v1/inventory/count                  — inventory count wizard
```

Auth `@login_required` + AUDITOR read-only; `ADMIN/ACCOUNTANT` write, `CHIEF` for cost method change.

## 4. Storage (SQLA)

```sql
products      (id PK, company_id IDX, code UNQ, name, uom, cost_method, standard_cost, active, checksum)
locations     (id PK, company_id IDX, warehouse_id, code, name, parent_id, type)
stock_moves   (id PK, company_id IDX, product_id IDX, qty DECIMAL, unit_cost, from_loc, to_loc, effective_date, shipment_id, state, checksum)
shipments     (id PK, company_id IDX, type, number, state)
stock_periods (id PK, company_id IDX, year, month, state UNQ)
cost_revisions(product_id, effective_date, old_cost, new_cost)
```

No 611 column; direct 152/156 via moves.

## 5. Costing semantics (VAS 02 §13-16 + TT99 Standard)

| Method | Recalc on | COGS 632 value |
|---|---|---|
| specific | each out picks lot cost | lot's unit_cost |
| wavg (moving) | each in: `avg=(prev_value+in_value)/(prev_qty+in_qty)` | avg at out date |
| fifo | queue lots | oldest lot(s) |
| standard | `standard_cost` fixed; variance = actual - standard → adjust 632 | standard_cost + variance |

Per-product choice: SKU A FIFO, SKU B WAVG allowed (TT99).

## 6. Non-functional

- Decimal all qty/cost, VND quantize 0.
- Pagination `page/page_size` 50/200 max for stock report.
- mypy strict + `ignore_missing` for flask; audit every POST.
- No deprecated 611; no perpetual/periodic flag.

