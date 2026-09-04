# Todo — Master Must-Have Slices (done only when code-review-and-quality Approve)

## Slice 1 — Party base (P0) ✅ Done — Approve `tasks/review-slice1.md`
- [x] Task 1.1: Party+Department domain+storage (2 tables, checksum)
- [x] Task 1.2: Party service (MST validate, duplicate 409, actor+reason, company isolation)
- [x] Task 1.3: Party web (POST/GET customer/supplier/employee, Department CRUD, AUDITOR 403)
- [x] Verify: `ruff 0, black 0, mypy 0, pytest 1011` — 11 new tests (7 unit + 4 integration)
- [x] Review: `code-review-and-quality` Approve → `tasks/review-slice1.md`

## Slice 2 — UOM + ProductCategory + Warehouse (P0) — pending next slice
- [ ] Task 2.1: UOM master (code/name/base/factor>0)
- [ ] Task 2.2: ProductCategory (code/name/parent/cost_method/account/tax_category)
- [ ] Task 2.3: Warehouse master (code/name/address/manager/account) + Location.warehouse_id FK migration
- [ ] Verify: 9 new tests, no 611, Product.uom still text (FK next)
- [ ] Review: Approve → `tasks/review-slice2.md`

## Slice 2 — UOM + ProductCategory + Warehouse (P0)
- [ ] Task 2.1: UOM master (code/name/base/factor>0)
- [ ] Task 2.2: ProductCategory (code/name/parent/cost_method/account/tax_category)
- [ ] Task 2.3: Warehouse master (code/name/address/manager/account) + Location.warehouse_id FK migration
- [ ] Verify: 9 new tests, no 611, Product.uom still text (FK next)
- [ ] Review: Approve → `tasks/review-slice2.md`

## Slice 3 — TaxCode + Lot + PriceList (P1)
- [ ] Task 3.1: TaxCode detail (code/rate/type/account)
- [ ] Task 3.2: Lot/Batch (lot_code/product/expiry/qty) + StockMove.lot_id
- [ ] Task 3.3: PriceList (product/uom/price/valid_from) → CostRevision history
- [ ] Verify: 6 new tests
- [ ] Review: Approve → `tasks/review-slice3.md`

## Final
- [ ] `pytest -q` ~1030 green, `git push`, codegraph sync
