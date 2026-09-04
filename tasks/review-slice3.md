# Review Slice 3 — TaxCode + Lot + PriceList

## Context
- Implements statutory edge masters: TaxCode detail (TT99 3331/1331), Lot/Batch (Specific/FIFO true), PriceList (Misa bảng giá → CostRevision history). Extends SystemSettings + Inventory, StockMove.lot_id, no 3P.

## Correctness
- [x] TaxCode: code unique/company, rate -1/0/5/8/10, type input/output/both, account 1331/3331, duplicate 409, invalid rate ValueError
- [x] Lot: lot_code/product/expiry/qty>=0, list by company+product, StockMove.lot_id nullable migration safe
- [x] PriceList: product/uom/price>=0/valid_from, history list, CostRevision seam (PriceList per date → standard variance auditable)
- [x] Edge: invalid tax rate 7 rejected, negative price rejected, lot qty negative rejected, PN/* series seeded in test
- [x] Tests: 3 unit TaxCode (create, duplicate, invalid) + 2 integration (TaxCode CRUD duplicate 422, Lot+Price CRUD + shipment with lot_id) — 5 green

## Readability
- [x] Names clear: TaxCode/Lot/PriceList, lot_code/expiry/valid_from
- [x] Service 20 lines TaxCode, Inventory Lot/Price 30 lines each — simple
- [x] No clever, DTZ011 noqa intentional (valid_from or today)

## Architecture
- [x] Lego: SystemSettings TaxCodeModel + SQLAlchemyTaxCodeRepository + TaxCodeService audit + web POST/GET /tax-codes; Inventory LotModel/PriceListModel + service + web POST/GET /inventory/lots|price-lists
- [x] Wiring: app.tax_code_service, init_tax_code_service, TaxCodeModel in SetBase (same Base), Lot/Price in InvtyBase, alembic already aggregates Base (no new Base)
- [x] No cross joins, company isolation, primitives only

## Security
- [x] ADMIN only for TaxCode (ADMIN_ROLES), AUDITOR 403 for Lot/Price write, actor+reason, SQLA param

## Performance
- [x] Indexed company_id+code/product_id, no N+1, list by company_id

## Verification
- [x] ruff 0, black 0, mypy src/bricks/system_settings src/bricks/inventory 0
- [x] pytest tests/unit/system_settings/test_tax_code_service.py tests/integration/test_slice3_api.py -q 5 passed
- [x] pytest tests -q 1023 passed

## Verdict
- [x] **Approve** — Ready to merge slice 3. Done only when pass, now pass.
