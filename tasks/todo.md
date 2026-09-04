# Todo — Master Must-Have Slices (done only when code-review-and-quality Approve)

## Slice 1 — Party base (P0) ✅ Done — Approve `tasks/review-slice1.md`
- [x] Task 1.1: Party+Department domain+storage (2 tables, checksum)
- [x] Task 1.2: Party service (MST validate, duplicate 409, actor+reason, company isolation)
- [x] Task 1.3: Party web (POST/GET customer/supplier/employee, Department CRUD, AUDITOR 403)
- [x] Verify: `ruff 0, black 0, mypy 0, pytest 1011` — 11 new tests (7 unit + 4 integration)
- [x] Review: `code-review-and-quality` Approve → `tasks/review-slice1.md`

## Slice 2 — UOM + ProductCategory + Warehouse (P0) ✅ Done — Approve `tasks/review-slice2.md`
- [x] Task 2.1: UOM master (code/name/base/factor>0)
- [x] Task 2.2: ProductCategory (code/name/parent/cost_method/account/tax_category)
- [x] Task 2.3: Warehouse master (code/name/address/manager/account) + Location.warehouse_id FK migration
- [x] Verify: 7 new tests (4 unit + 3 integration), ruff 0 black 0 mypy 0, pytest 1018
- [x] Review: Approve → `tasks/review-slice2.md`

## Slice 3 — TaxCode + Lot + PriceList (P1) ✅ Done — Approve `tasks/review-slice3.md`
- [x] Task 3.1: TaxCode detail (code/rate/type/account)
- [x] Task 3.2: Lot/Batch (lot_code/product/expiry/qty) + StockMove.lot_id
- [x] Task 3.3: PriceList (product/uom/price/valid_from) → CostRevision history
- [x] Verify: 5 new tests (3 unit + 2 integration), ruff 0 black 0 mypy 0
- [x] Review: Approve → `tasks/review-slice3.md`

## Final
- [x] `pytest -q` 1023 green, `git push`, codegraph sync
