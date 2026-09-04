# Review Slice 8 — Master tables migration (slices 1–4, 6)

## Context
- Slices 1–4 + 6 shipped code with zero migrations: 8 new tables + 3 new columns + 1 index exist only via `create_all`. Alembic-managed DBs lack them → upgrade path broken. Hand-written (autogenerate broken repo-wide, pre-existing FK error — untouched per surgical rule).

## Correctness
- [x] Covers exactly what slices added: `parties`, `departments`, `uoms`, `inventory_categories`, `inventory_warehouses`, `inventory_lots`, `inventory_price_lists`, `tax_codes` + `inventory_products.uom_id/category_id` + `inventory_moves.lot_id` + `ix_moves_company_product_state`
- [x] Column types mirror models (`String(36)` ids, `Numeric(18,6)` factor, `Numeric(18,2)` qty/price, nullable new cols)
- [x] Verified on scratch DB: `upgrade head` creates 8/8 tables; downgrade −1 removes them; re-upgrade clean; single head (`f4a9c1d2e7b5`)
- [x] Idempotent guards (`has_table`/`has_column`/`has_index`) → safe on app-lineage DBs (tables exist via `create_all`) and alembic-lineage DBs; re-runnable
- [x] Found + disclosed: alembic-lineage DBs also lack inventory base tables (pre-date migrations, pre-existing) — out of scope, noted below; app lineage (real PROD path) unaffected
- [x] Full suite 1045 passed (no behavior change; migration file excluded from app imports)

## Readability
- [x] One helper trio (`_has_table/_has_column/_has_index`) + `_create_table` with index tuples; per-table sections labeled by slice; downgrade mirrors upgrade in reverse

## Architecture
- [x] Chain correct: `down_revision 9c1a2b3d4e5f` (prior head); no model imports in migration (frozen schema, survives future model edits)
- [x] Follow-up (separate): backfill base inventory tables for alembic-only lineage; dedicated variance GL account (Slice 5 note stands)

## Security / Performance
- [x] No input surface, no data migration (all new structures nullable/empty); DDL only; SQLite-safe (no transactional-DDL assumption — alembic already handles)

## Verification
- [x] `ruff check` pass (after --fix), `black --check` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (129 files)
- [x] `pytest -q` 1045 passed
- [x] Scratch upgrade/downgrade/re-upgrade cycle green

## Verdict
- [x] **Approve** — merge Slice 8.
