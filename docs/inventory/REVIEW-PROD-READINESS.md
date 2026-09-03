# REVIEW — Inventory Bricks PROD Readiness (BA Lead 20y + Chief Accountant 20y)

| | |
|---|---|
| Module | Inventory — `stock + warehouse + cost` (HTK per VAS 02, TT99/TT58) |
| Date | 2026-09-03 |
| Reviewers | BA Lead 20y ERP/SME + Chief Acc VACPA 20y + Legal Research (137 docs, vbpl/mof/gdt/Big4/Tryton 8.0/Misa/Fast/Bravo) |
| Gate | ruff → black → mypy strict → pytest 988 (no inventory) |
| Verdict | **NOT PROD — brick missing** |

## 1. TL;DR

```
Inventory bricks DO NOT EXIST in src/bricks/* → CAN NOT operate PROD.
Purchases + Sales + Voucher + Ledger + Fixed Assets exist, but no stock ledger.
Any sale/purchase without stock check will oversell, misstate COGS, break TT99 costing.
```

| Track | Verdict | Reason |
|---|---|---|
| Product master + UOM + warehouse/location | **NO** | No models |
| Stock moves (in/out/internal), shipment, period | **NO** | Tryton stock.Move pattern absent |
| Cost method per product (specific/WAVG/FIFO/Standard) | **NO** | TT99 4th method not modeled |
| 152/153/154/155/156/611 logic, NRV provision | **NO** | 611 abolished per TT99 yet code still references? |
| Inventory count + reconciliation + period lock | **NO** | No `stock.period` |
| Integration with purchases (in), sales (out), COGS | **NO** | Sales currently Nợ 131/Có 511 only, no 632 |
| Reports (tồn kho, turnover) | **NO** | No warehouse reporting |

## 2. Repo evidence (codegraph sync 2026-09-03)

```
src/bricks/* 18 bricks:
 audit_log, bank_cash, coa, company, cost_centers, currencies, document_conversion,
 financial_statements, fiscal_year_period, fixed_assets, invoice, ledger,
 payment_terms, purchases, system_settings, tools_equipment, user_master_data, voucher, xml_ingest

MISSING: inventory / stock / product / warehouse
Grep "class.*Stock|Inventory|Warehouse" → 0 hits (only tools_equipment Inventory unrelated)
Purchase brick creates SupplierInvoice + audit but NO stock move (Gate R-P1..P7 only FY/COA/duplicate)
Invoice brick posts to 131/511/3331 via AutoJournal, no 632/155/156 branch
Ledger reads voucher lines only → stock value not visible
```

**Test gate** `pytest 988` has 0 inventory tests → coverage 0%.

## 3. Why GAP is P0 for PROD SME

- SME manufacturing/trading core is HTK: per VAS 02 §03 HTK = hàng hóa, thành phẩm, dở dang, NVL/CCDC. 90% SMEs hold stock → without brick, financials B01 misstate TSNH, B02 misstate giá vốn.
- TT99 abolishes 611 (Purchases proxy) and perpetual/periodic dichotomy → old workaround `152→611→632` no longer compliant. Must track via stock moves with cost price revision.
- TT99 allows per-item costing method (different SKUs different method) + Standard Cost → requires `cost_price_method` per product, not global.
- Misa/Fast/Bravo all require warehouse + location + lot/serial optional + cost recompute → our ledger has no warehouse dimension.

## 4. Laws double-checked (2026-09-03) — outdated REMOVED

```
OUTDATED                          REPLACED BY (ACTIVE)
─────────────────────────────    ─────────────────────────────────────
TT200/2014/TT-BTC Ch.II §22-30 → TT99/2025/TT-BTC (27/10/2025) FY≥01/01/2026
TT133/2016/TT-BTC (SME)         → TT58/2026/TT-BTC (SME, small)
VAS 02 LIFO allowed              TT99+VAS 02: LIFO disclosure still if used but Standard Cost added; LIFO less used
TK 611 Purchases                 → abolished per TT99, use direct 152/156 via moves
Perpetual vs Periodic choice     → abolished: always track move-level; method "kê khai thường xuyên" is default through moves + period
QĐ 15/2006                       → TT99
```

Active drivers for Inventory:

- **VAS 02** (QĐ 149/2001/QĐ-BTC 31/12/2001) §04-§16: HTK at original price (purchase+processing+direct), NRV if lower, methods §13 a/b/c/d = specific/WAVG/FIFO/LIFO (§14-§16) + TT99 adds Standard Cost.
- **TT99/2025** Ch.III § inventory: standard cost new, per-item method choice (different SKUs different), materials >12m present as long-term not inventory, doc required `Internal Accounting Policy` for COA custom.
- **TT58/2026** SME simplifies but same 4 methods.
- **TT99** also: account 611 abolished, cost price revision via wizard pattern (Tryton Cost Price Revision).
- **Luật Kế toán 88/2015** Art.11 10y retention.

Verified via: vbpl.vn (VAS 02 en), thuvienphapluat, mof.gov.vn, indochinalink 2025-01-03, forvismazars 2026-07-24, tryton docs 8.0.0 2026-04-20 (stock module design), vietanlaw, vvic, atax.

Tryton 8.0 latest active; Misa SME 2025 R12 active (tồn kho: kho, vật tư, tính giá TB/FIFO/đích danh/chuẩn), Fast Active, BravoERP Active.

## 5. Comparison vs ERP standards (core→edge)

| Concern | Misa SME 2025 | Fast | BravoERP | Our repo |
|---|---|---|---|---|
| Product master + UOM | catalog + nhóm VTHH, đơn vị tính | same | same | none |
| Warehouse/location hierarchy | kho → vị trí (parent) | same | same + bin | none |
| Stock moves (Import/Export/Transfer) | PN, PX, CĐ kho | same | Shipment internal | none |
| Cost method per product | TB tháng, TB di động, FIFO, đích danh, chuẩn (Standard) | same | same + actual | single vat only |
| COGS auto 632 | PX → 632 per method | same | same | manual voucher only |
| Period / lock | kỳ kiểm kê, khóa kho | same | stock.period | FY lock only, no stock period |
| Reports | Tồn kho, NXT, thẻ kho, quay vòng | NXT, turnover | inventory/daily | ledger only voucher |
| COA 152/153/154/155/156 | maps via move valuation | same | same | no mapping |

## 6. Roadmap to PROD (roadmap.md §5) — 5 sprints needed

S1: Product + UOM + Warehouse/Location + Stock Move (in/out/internal) + Period
S2: Cost method per product (4 methods) + cost recompute + 632
S3: NRV provision + 611 migration removal + 152/156 mapping
S4: Inventory count + reconciliation + period lock + audit
S5: Reports (NXT, thẻ kho, turnover) + API + FY integration

Without these, enabling sales purchases in PROD risks oversell and TT99 non-compliance.

## 7. Recommendation

- **Today**: block PROD inventory transactions: feature flag `inventory.enabled=false`, force purchases/sales via voucher manual until brick built.
- Do not reuse `tools_equipment` for HTK — separate brick `inventory` with Tryton-like Move/Shipment/Period design per specs.md.
- Before PROD: S1–S5 closed + migrate old 611 references → direct 152/156.

---
*BA Lead + Chief Acc review. Codegraph + git sync verified. Law re-checked 2026-09-03.*
