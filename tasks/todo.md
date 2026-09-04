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

## Slice 4 — Product link FK UOM/Category ✅ Done — Approve `tasks/review-slice4.md`
- [x] Product `uom_id`/`category_id` optional nullable, legacy `uom` text kept (dual-read)
- [x] Service validates existence + same-company (422), `uom_repo` injected via `app.py`
- [x] Web accepts/serializes `uom_id`/`category_id`
- [x] Verify: 4 new tests (3 unit RED→GREEN + 1 integration), ruff 0 black 0 mypy 0, pytest 1027
- [x] Review: Approve → `tasks/review-slice4.md`
- [ ] Follow-up (separate): alembic migration for `uom_id`/`category_id` cols (autogenerate blocked by pre-existing `tools_equipment → cost_centers` FK error)

## Slice 5 — Variance + costing split ✅ Done — Approve `tasks/review-slice5.md`
- [x] Pure `costing.py`: `moving_average_unit`/`specific_out_unit`/`fifo_out_unit`/`split_standard`/`fifo_lots_from_moves`
- [x] Service delegates; STANDARD out books variance into 6321 line + audit split (`cogs_total`, `variance_total`)
- [x] Verify: 6 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1033
- [x] Review: Approve → `tasks/review-slice5.md`
- [ ] Follow-up (separate): dedicated variance account + `resolve_chart_role("variance")`; alembic migration for `uom_id`/`category_id` cols

## Slice 6 — Stock perf ✅ Done — Approve `tasks/review-slice6.md`
- [x] Composite index `ix_moves_company_product_state` on `(company_id, product_id, state)`
- [x] Stock list pagination `page`/`page_size` (defaults 1/50, max 200, ledger-style meta)
- [x] Verify: 4 new tests (3 unit RED→GREEN + 1 integration), ruff 0 black 0 mypy 0, pytest 1037
- [x] Review: Approve → `tasks/review-slice6.md`
- [ ] Follow-up (separate): single-query `SUM(qty)` aggregation; `get_stock_value` same treatment

## Slice 7 — Sales GDT real-sign seam (no 3P) ✅ Done — Approve `tasks/review-slice7.md`
- [x] Pure `einvoice.py`: GDT-tagged XML builder + ready-guard + mock signer (sha256)
- [x] Service `issue_einvoice` with injected `signer` port; web delegates (no more `_repo`/`_audit` privates)
- [x] Verify: 8 new tests RED→GREEN (incl. GDT round-trip), ruff 0 black 0 mypy 0, pytest 1045
- [x] Review: Approve → `tasks/review-slice7.md`
- [ ] Follow-up (separate): real CA signer + GDT sender + XSD pin; flip `sales.e_invoice_enabled`

## Slice 8 — Master tables migration (slices 1–4, 6) ✅ Done — Approve `tasks/review-slice8.md`
- [x] Hand-written `f4a9c1d2e7b5` (autogenerate broken repo-wide, pre-existing FK error untouched)
- [x] 8 tables + 3 columns + 1 composite index; idempotent guards for both DB lineages
- [x] Verify: scratch upgrade/downgrade/re-upgrade green, single head, ruff 0 black 0 mypy 0, pytest 1045
- [x] Review: Approve → `tasks/review-slice8.md`
- [ ] Follow-up (separate): backfill base inventory tables for alembic-only lineage; dedicated variance GL account

## Config Slice 1 — Law thresholds as CONFIG flags ✅ Done — Approve `tasks/review-config-slice1.md`
- [x] `non_cash_threshold` (default 5tr) + `max_einvoice_series` (default 15) versioned flags
- [x] Series-cap check reads config; purchases threshold wiring deferred to Slice 2
- [x] Verify: 5 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1050
- [x] Review: Approve → `tasks/review-config-slice1.md`
## Config Slice 2 — Threshold port + 8% exclusion table ✅ Done — Approve `tasks/review-config-slice2.md`
- [x] `threshold_of` port stamps per-invoice threshold; old rows fall back to 5tr
- [x] `exclusion_of` port; exclusions table seeded from NĐ174, panel CRUD, gates delegate
- [x] Migration `a1b2c3d4e5f6` guarded both lineages; scratch up/down/re-up green
- [x] Verify: 7 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1057
- [x] Review: Approve → `tasks/review-config-slice2.md`
## Config Slice 3 — E-invoice flag + variance account ✅ Done — Approve `tasks/review-config-slice3.md`
- [x] `sales_einvoice_enabled` bool flag default False; service port defaults allow; 403 `E_INVOICE_DISABLED`
- [x] `variance_account` flag default "" (= legacy ride); set + ≠ COGS → balanced 3-line voucher; chart roles added
- [x] Migration `b2c3d4e5f6a7` guarded; scratch up/down/re-up green, single head
- [x] Verify: 5 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1062
- [x] Review: Approve → `tasks/review-config-slice3.md`

## Opening S1 — GL + bank + lock gate ✅ Done — Approve `tasks/review-opening-s1.md`
- [x] `opening_balance` brick (5-file Lego): batch DRAFT/LOCKED, GL single-side, bank rows
- [x] Voucher go-live gate grandfathered (no batches → skip); 409 `NO_OPENING_LOCK` otherwise
- [x] Migration `c3d4e5f6a7b8` guarded; scratch up/down/re-up green, single head
- [x] Verify: 9 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1071
- [x] Review: Approve → `tasks/review-opening-s1.md`
## Opening S2 — Counterparty AR/AP + aging hook ✅ Done — Approve `tasks/review-opening-s2.md`
- [x] `CounterpartyBalance` (party FK, side, proof) + table + repo + endpoint
- [x] R-O03 tie enforced at lock; locked 131 rows feed ledger AR aging as current
- [x] Migration `d4e5f6a7b8c9` guarded; scratch up/down/re-up green, single head
- [x] Verify: 6 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1077
- [x] Review: Approve → `tasks/review-opening-s2.md`
## Opening S3 — Stock opening by SKU×warehouse ✅ Done — Approve `tasks/review-opening-s3.md`
- [x] `StockOpening` rows (qty/value/lot/receipt detail) + table + repo + endpoint
- [x] Materialize DONE moves via inventory port (no GL — opening GL covers); R-O02 tie at lock
- [x] Build-order cycle broken via late-bound holder (commented)
- [x] Migration `e5f6a7b8c9d0` guarded; scratch up/down/re-up green, single head
- [x] Verify: 6 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1083
- [x] Review: Approve → `tasks/review-opening-s3.md`
## Opening S4a — FA + bank tie ✅ Done — Approve `tasks/review-opening-s4a.md`
- [x] `AssetOpening` rows + table + endpoint; materialize FA with carried accumulated
- [x] Lock ties: bank↔112x, FA GTCL↔211−214 (R-O04)
- [x] `create_asset` optional accumulated (backward compat)
- [x] Migration `f6a7b8c9d0e1` guarded; scratch up/down/re-up green, single head
- [x] Verify: 5 new tests RED→GREEN, ruff 0 black 0 mypy 0, pytest 1088
- [x] Review: Approve → `tasks/review-opening-s4a.md`
- [ ] Next: Opening S4b — CCDC opening via elapsed-allocation backfill + 242 tie

## Final
- [x] `pytest -q` 1023 green, `git push`, codegraph sync
