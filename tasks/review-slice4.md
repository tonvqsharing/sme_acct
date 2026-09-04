# Review Slice 4 — Product link FK UOM/Category

## Context
- Links `Product` to `UOM` + `ProductCategory` via optional nullable FKs. Legacy `uom` text kept (dual-read). No auto cost-method default, no 3P.

## Correctness
- [x] Matches spec: optional `uom_id`/`category_id`, existence + same-company guard, legacy text-only products still pass
- [x] Edge: unknown UOM 422, cross-company category 422, no actor/reason still ValueError, duplicate SKU unchanged
- [x] Tests: 3 unit (`test_product_links.py` RED→GREEN) + 1 integration API link round-trip — state-based asserts on returned ids
- [x] Full suite: 1027 passed (1023 + 4 new)

## Readability
- [x] Names follow existing: `uom_id`, `category_id`, error strings contain `uom`/`category` for API mapping
- [x] No clever code; validation block mirrors existing style; ~20 new service lines

## Architecture
- [x] Lego kept: domain pure (2 optional UUIDs), storage nullable `String(36)` cols + round-trip in `_to_product`/`update_product`
- [x] No cross-brick storage import: `uom_repo` injected via `app.py` port (`SQLAlchemyUOMRepository`), fallback `repo.get_uom` for fakes; category via existing `repo.get_category`
- [x] Wiring order safe: UOM brick constructed before inventory in `app.py`; same `uom_repo` reused for `UOMService`
- [x] No migration file: `alembic revision --autogenerate` blocked by pre-existing `tools_equipment.cost_center_id → cost_centers` FK error (untouched per surgical rule); nullable cols covered by `create_all` in tests — migration follow-up separate

## Security
- [x] Tenant isolation enforced on both links (company match); `@login_required` + `_require_write` unchanged; AUDITOR still 403; no secrets; SQLA params only

## Performance
- [x] +2 lookups max per product create (indexed `id` gets); no N+1 (single create path); no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (127 files)
- [x] `pytest -q` 1027 passed

## Verdict
- [x] **Approve** — merge Slice 4.
