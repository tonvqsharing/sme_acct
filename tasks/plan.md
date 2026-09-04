# Implementation Plan: Master Data Must-Have (Party/UOM/Category/Warehouse/Tax/Lot/Price)

## Overview
Build 11 missing master objects (Customer/Supplier/Employee/Department/UOM/ProductCategory/Warehouse/TaxCode/Lot/PriceList) ordered core→edge per TT99/TT58, Tryton party, Misa/Fast/Bravo. Each vertical slice delivers domain+storage+service+web+tests and is done only when ruff→black→mypy→pytest + code-review-and-quality Approve. No 3P (WMS/BOM) this version.

## Architecture Decisions
- New brick `party` for Party + Customer/Supplier/Employee + Department (single Tryton party base with role flags vs 3 separate masters — fewer joins, Misa parity)
- `uom` standalone brick (reused by inventory product), `product_category` inside inventory, `warehouse` inside inventory, `tax_code` inside system_settings, `lot` inside inventory, `price_list` inside inventory — keeps Lego 5-file per brick
- All masters: `code unique/company`, `company_id FK`, `active`, `checksum GENESIS`, `company isolation`, `AUDITOR 403`
- Domain pure, ports primitives only, storage Mapped, web `@login_required`

## Task List

### Phase 0: Discovery (domain-modeling + spec-driven)
- Read `docs/inventory/*`, `docs/sales/*`, VAS 02, TT99 §13, Tryton party/product/uom/warehouse docs, Misa masters — done.

### Phase 1: Slice 1 — Party base (P0 core, blocks AR/AP)
**Task 1.1: Party domain + storage** — Party(id,company_id,code,name,mst,address,phone,email,is_customer/is_supplier/is_employee,active,checksum) + Department(code,name,parent,manager). 2 tables.
**Task 1.2: Party service** — `create_party` MST `^[1-9]\d{2}(-\d{3})?$` + 10/13 digit fallback, duplicate code/MST per company 409, active guard, `actor+reason` required, `find_open_period` optional? No FY for master but audit chain.
**Task 1.3: Party web** — `POST /party` `GET /party?company_id&role=customer/supplier/employee` + Department CRUD, AUDITOR 403 write.
**Verification:** `pytest tests/unit/party + integration` 10 tests, ruff/black/mypy clean.
**Files:** `src/bricks/party/*` (5 files), `alembic/env.py`, `src/app.py`, `tests/unit/party/*`, `tests/integration/test_party_api.py`

#### Checkpoint 1
- [ ] Slice 1 tests pass
- [ ] `code-review-and-quality` Approve (5 axes checklist filed `tasks/review-slice1.md`)

### Phase 2: Slice 2 — UOM + ProductCategory + Warehouse (P0)
**Task 2.1: UOM master** — `UOM(code unique/company, name, base_uom_id, factor Decimal, active)` factor>0, base cycle guard.
**Task 2.2: ProductCategory** — `code,name,parent, cost_method default, account 152/156, tax_category for 8%`
**Task 2.3: Warehouse header** — `Warehouse(code, name, address, manager party_id, account_type)` + migrate `Location.warehouse_id FK Warehouse.id` (was loose UUID)
**Verification:** 6 unit + 3 integration, no 611, `Product.uom` free text → FK UOM.id next slice (deferred to P1 to keep slice small)
**Files:** `src/bricks/uom/*`, `src/bricks/inventory/*` category/warehouse add, tests

#### Checkpoint 2
- [ ] Slice 2 tests pass
- [ ] Review Approve

### Phase 3: Slice 3 — TaxCode + Lot + PriceList (P1 statutory edge)
**Task 3.1: TaxCode detail** — `code, rate -1/0/5/8/10, type input/output, account 1331/3331` beyond enum
**Task 3.2: Lot/Batch** — `lot_code, product_id, expiry, qty` + `StockMove.lot_id`
**Task 3.3: PriceList** — `product_id, uom_id, price, valid_from, standard_cost history` → `CostRevision`
**Verification:** 6 tests, `Product.standard_cost` stays single until PriceList cutover (flag)
**Files:** `src/bricks/system_settings/*` tax_code, `src/bricks/inventory/*` lot/price

#### Checkpoint 3 — Complete
- [ ] All 3 slices Approve
- [ ] `pytest 1000→~1030` green, `mypy` overrides added
- [ ] `git sync` + codegraph sync

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| MST validation strict vs legacy 10-digit | High | regex `^[1-9]\d{2}(-\d{3})?$` + 10/13 fallback like sales, duplicate 409 |
| Warehouse migrate breaks existing Location | Med | Keep `Location.warehouse_id` nullable, add FK later, dual-read |
| UOM factor cycle | Low | Guard base cycle, simple factor>0 |

## Open Questions
- Party single table vs 3 masters? Chose single with role flags — fewer joins, Tryton party parity; 3 masters would duplicate MST logic.
