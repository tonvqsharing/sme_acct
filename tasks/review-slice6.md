# Review Slice 6 — Stock perf (index + pagination)

## Context
- `get_stock_qty/value` scan all DONE moves in Python per product. Adds DB composite index + ledger-style pagination on stock list. No behavior change to quantities.

## Correctness
- [x] Index `ix_moves_company_product_state` on `(company_id, product_id, state)` matches the hottest filter (`list_moves` product+state, `get_stock_*` per product)
- [x] Pagination `page`/`page_size` clamped like ledger (page ≥ 1, size 1–200); defaults (1, 50) keep all existing callers green
- [x] Invalid `page=x` → 422; response gains additive `page`/`page_size` meta (existing `data` shape untouched)
- [x] Tests: 3 unit (index metadata, paginate slices, defaults return all) RED→GREEN + 1 integration (3 products, page 1/2 meta, bad page 422); full suite 1037 passed (1033 + 4)

## Readability
- [x] 8-line service diff, 10-line web diff; clamp mirrors ledger convention; no clever code

## Architecture
- [x] Index declared in owning `StockMoveModel.__table_args__`; no query rewrite — same filters now index-backed
- [x] Pagination at service boundary like ledger; per-product qty/value calls remain (bounded by page_size now)
- [x] Follow-up (separate): single-query `SUM(qty)` aggregation to remove per-product round-trips; `get_stock_value` same treatment

## Security
- [x] No input-surface change beyond int params with 422 on garbage; tenant isolation untouched; SOD untouched

## Performance
- [x] Hot path `(company, product, state)` now indexed; stock list bounded to ≤200 rows/page (was unbounded)
- [x] Quantified: no benchmark infra in repo; gain is index-hit on the per-product DONE-moves filter, not measured — stated, not claimed

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (128 files)
- [x] `pytest -q` 1037 passed

## Verdict
- [x] **Approve** — merge Slice 6.
