# Review Slice 2 — UOM + ProductCategory + Warehouse

## Context
- Implements missing masters: UOM (Tryton UOM), ProductCategory (nhóm VTHH per TT99 + 8% tax_category), Warehouse header (Misa Kho). Extends Inventory brick with category/warehouse tables, keeps Product.uom text FK next slice.

## Correctness
- [x] UOM: code unique/company, factor>0, base cycle guard self ref, duplicate 409, company isolation
- [x] Category: code/name/parent, cost_method enum, account_code 152/156, tax_category for 8%
- [x] Warehouse: code/name/address/manager/account, Location.warehouse_id FK nullable migration safe
- [x] Edge: factor 0 ValueError, base not in company ValueError, invalid code 422
- [x] Tests: 4 unit UOM (basic, duplicate, factor, base) + 3 integration (UOM CRUD base 10, category+warehouse+location link, product with new masters) — 7 green

## Readability
- [x] Names clear: UOM/Category/Warehouse, factor, base_uom_id, tax_category
- [x] Service 58 lines UOM, Inventory category/warehouse 20 lines each — simple
- [x] No clever, no 611

## Architecture
- [x] Lego: UOM 5-file brick Base UOMBase, Inventory 2 new tables ProductCategoryModel/WarehouseModel, ports primitives, company isolation
- [x] Wiring: UOMBase.create_all, uom_bp, SQLAlchemyUOMRepository, UOMService audit, app.uom_service, alembic UOMBase (21 Bases)
- [x] No cross joins, UOM not yet FK enforced on Product (deferred to keep slice small)

## Security
- [x] AUDITOR 403 write, actor+reason, company isolation, SQLA param

## Performance
- [x] Indexed company_id+code, no N+1, list by company_id

## Verification
- [x] ruff 0, black 0, mypy src/bricks/uom src/bricks/inventory 0
- [x] pytest tests/unit/uom tests/integration/test_uom_inventory_slice2_api -q 7 passed
- [x] pytest tests -q 1018 passed (1011+7)

## Verdict
- [x] **Approve** — Ready to merge slice 2. Done only when pass, now pass.
