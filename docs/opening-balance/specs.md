# Specs — Opening Balance Brick

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-09-04 |
| Brick | `src/bricks/opening_balance/` → `domain.py` pure + `services.py` ports + `storage.py` SQLA + `web_adapter.py` Flask |

## 1. Domain model (target v1, MISA SME 2026 parity)

```python
@dataclass
class OpeningBatch:
    company_id: UUID
    fiscal_year_id: UUID      # opening belongs to year N start
    source: BatchSource       # MANUAL | EXCEL | YEAR_ROLL
    state: BatchState = DRAFT # DRAFT → LOCKED
    id: UUID = ...
    checksum: str = ""

@dataclass
class GLBalance:              # Số dư tài khoản
    batch_id: UUID
    account_code: str         # ACTIVE detail only, regime-aware
    debit: Decimal = 0        # Nợ — exactly one side > 0
    credit: Decimal = 0       # Có
    currency_code: str = "VND"
    fx_amount: Decimal | None = None

@dataclass
class CounterpartyBalance:    # công nợ KH/NCC/NV (131/331/141/138/338)
    batch_id: UUID
    account_code: str
    party_id: UUID            # Party master FK, same company
    amount: Decimal           # signed: + receivable, − payable? No — side field
    side: str                 # "debit" | "credit"
    proof: bool = False       # non-cash proof flag (≥5tr AP)

@dataclass
class StockOpening:           # tồn kho VTHH
    batch_id: UUID
    product_id: UUID
    warehouse_id: UUID        # Warehouse header FK
    location_id: UUID | None
    qty: Decimal              # > 0
    total_value: Decimal       # ≥ 0; unit = value/qty derived
    lot_code: str | None = None
    expiry_date: date | None = None
    receipt_date: date | None = None   # required for FIFO/specific lots
    receipt_doc: str | None = None
    unit_cost: Decimal | None = None   # per-receipt price (FIFO/specific)

@dataclass
class AssetOpening:           # TSCĐ/CCDC/242 unified
    batch_id: UUID
    kind: str                 # "fixed_asset" | "ccdc" | "prepaid"
    code: str
    name: str
    original_cost: Decimal
    remaining_value: Decimal  # ≤ original_cost
    months_left: int          # ≥ 1 → feeds SL/allocation engines
    expense_account: str

@dataclass
class BankOpening:            # per bank account
    batch_id: UUID
    bank_account_id: UUID     # BankAccount master FK
    amount: Decimal
```

### State machine

```
Batch:   DRAFT ─post→ LOCKED ─reopen(CHIEF)→ DRAFT
Go-live: first live voucher requires LOCKED batch (else 409 NO_OPENING_LOCK)
```

## 2. Service contracts (ports — primitives only)

```python
class OpeningService:
    def create_batch(*, company_id, fiscal_year_id, source, actor, reason) -> OpeningBatch
    def post_gl(batch_id, *, lines:[{account_code, debit, credit, currency?}], actor, reason) -> None
    def post_counterparty(batch_id, *, rows:[...], actor, reason) -> None
    def post_stock(batch_id, *, rows:[...], actor, reason) -> None
    def post_assets(batch_id, *, rows:[...], actor, reason) -> None
    def post_bank(batch_id, *, rows:[...], actor, reason) -> None
    def reconcile(batch_id) -> ReconcileReport   # no mutation
    def lock(batch_id, *, actor: CHIEF/ADMIN, reason) -> None   # requires balanced
    def reopen(batch_id, *, actor: CHIEF, reason) -> None
    def roll_year(from_year_id, to_year_id, *, actor, reason) -> OpeningBatch  # close→open copy
```

Gates (order fixed):
```
1. actor+reason required
2. batch DRAFT (any post/lock on LOCKED → 409)
3. FY belongs to company; opening date = FY.start_date
4. account ACTIVE detail under regime; party/product/warehouse/bank same company + active
5. amounts: exactly one side > 0; qty > 0; remaining ≤ original; months ≥ 1
6. FIFO/specific rows need receipt_date+doc+unit_cost
7. lock requires reconcile balanced (ΣNợ = ΣCó AND subledger = GL per mapped account)
8. checksum sha256(prev|id|actor|state|canonical_rows|reason)
```

## 3. HTTP API (web_adapter.py — ONLY Flask file)

```
POST   /api/v1/opening-batches                        — create DRAFT
POST   /api/v1/opening-batches/<id>/gl                 — GL lines
POST   /api/v1/opening-batches/<id>/counterparties     — AR/AP rows
POST   /api/v1/opening-batches/<id>/stock              — SKU rows
POST   /api/v1/opening-batches/<id>/assets             — FA/CCDC rows
POST   /api/v1/opening-batches/<id>/bank               — bank rows
POST   /api/v1/opening-batches/<id>/excel              — multipart ≤10 files, template-validated
GET    /api/v1/opening-batches/<id>/reconcile          — report, no mutation
POST   /api/v1/opening-batches/<id>/lock               — CHIEF/ADMIN, balanced only
POST   /api/v1/opening-batches/<id>/reopen             — CHIEF only
POST   /api/v1/opening-batches/roll-year               — close N → open N+1
GET    /api/v1/opening-batches/templates/<kind>        — Excel template download
```

Auth `@login_required` all; AUDITOR writes → 403.

## 4. Storage

```sql
opening_batches   (id PK, company_id IDX, fiscal_year_id, source, state, checksum)
opening_gl        (id PK, batch_id IDX, account_code, debit, credit, currency_code, fx_amount)
opening_counterparty (id PK, batch_id IDX, account_code, party_id IDX, side, amount, proof)
opening_stock     (id PK, batch_id IDX, product_id IDX, warehouse_id, location_id, qty, total_value,
                   lot_code, expiry_date, receipt_date, receipt_doc, unit_cost)
opening_assets    (id PK, batch_id IDX, kind, code, name, original_cost, remaining_value, months_left, expense_account)
opening_bank      (id PK, batch_id IDX, bank_account_id, amount)
```

Stock rows materialize as DONE moves (`from_loc=None`, cost = value/qty or per-receipt) so NXT/costing work day one. FA rows seed TSCĐ/CCDC masters + remaining schedules. Counterparty rows feed AR/AP aging `as_of` FY start.

## 5. Reconcile rules (R-Oxx detail in processes-rules.md)

| Check | Formula |
|---|---|
| Trial balanced | ΣNợ(GL) = ΣCó(GL) ±0.01 |
| SKU = GL | Σ StockOpening.total_value by account = GL debit of 152/153/155/156/157/158 |
| Party = GL | Σ Counterparty by account = GL of 131/331/141/138/338 |
| Bank = GL | Σ BankOpening = GL 112x |
| FA = GL | Σ remaining TSCĐ = 211−214 tie; CCDC = 242 tie |

## 6. Non-functional

- Decimal everywhere, VND `quantize(1)`; `dict[str,Any]` strict mypy.
- Excel: `.xlsx` only, ≤10 files, header-validated, valid-rows-only import + error sheet.
- Period: opening date = FY.start_date; posting before lock allowed only for opening batch.
- Audit every mutation; 10y retention.
