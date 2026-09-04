# Use Cases — Opening Balance

## Actors

```
Accountant (KT) ── enters opening rows, imports Excel
Chief Accountant ─ locks/reopens, approves conversion maps
Auditor ────────── read-only reconcile + verify chain
System ─────────── gates, materialize moves/masters, checksum, audit
Prior books ────── Excel / old vendor export (untrusted input)
```

## UC-01 — GL opening (happy)

```
Pre: company + FY 2026 OPEN, COA seeded
1. KT POST /opening-batches {company_id, fiscal_year_id, source: MANUAL} → DRAFT
2. KT POST /<id>/gl {lines:[{111: Nợ 500tr}, {4111: Có 500tr}]} → 201
3. GET /<id>/reconcile → {balanced: true, ...}
4. CHIEF POST /<id>/lock → LOCKED
Alt: unbalanced lines accepted at entry (409 only at lock) — matches MISA two-step
```

## UC-02 — AR by customer (happy)

```
1. Parties KH-001 (MST valid) exist
2. KT POST /<id>/counterparties {rows:[{1311, KH-001, debit 200tr}]} → 201
3. AR aging as_of FY.start shows KH-001 200tr bucket current
Alt: ≥5tr AP row without proof → stored with proof:false, deductibility PENDING later
Exc: unknown party → 404; cross-company party → 422; AUDITOR → 403
```

## UC-03 — Stock by SKU×warehouse (happy)

```
1. Products SKU-001 (FIFO) + warehouse Kho A exist
2. KT POST /<id>/stock {rows:[{SKU-001, Kho A, qty 100, total_value 1M}]} → 201
3. System materializes DONE move (from None, unit 10k) → NXT shows 100
4. GET reconcile → SKU total 1M = GL 152 debit 1M ✓
Alt (FIFO lots): rows per receipt {date, doc, qty, unit_cost} → queue replays
Exc: qty ≤ 0 → 422; unknown SKU → 404; value/qty mismatch vs GL → reconcile warn
```

## UC-04 — TSCĐ opening (happy)

```
1. KT POST /<id>/assets {kind: fixed_asset, code: TSCD-01, original 1.2T, remaining 800tr, months_left 80}
2. System seeds FA master + accumulated 400tr → monthly SL 10tr from FY start
3. GET reconcile → 211−214 tie ✓
```

## UC-05 — Excel import (happy)

```
1. KT GET /templates/stock → .xlsx with headers
2. KT POST /<id>/excel files:[stock.xlsx] → {imported: 480, errors: [{row 12: unknown SKU}]}
3. Valid rows persist; error sheet returned; re-upload after delete-reload
Exc: >10 files → 422; wrong headers → 422 with expected list; all-invalid → 422, nothing persisted
```

## UC-06 — Go-live lock (happy)

```
Pre: reconcile balanced all checks green
1. CHIEF POST /<id>/lock → LOCKED + audit
2. First live voucher allowed (gate sees LOCKED batch)
Alt: unbalanced → 409 UNBALANCED with diff lines
Exc: ACCOUNTANT lock → 403; post-lock edit → 409, must CHIEF reopen with reason
```

## UC-07 — Year-roll (happy)

```
Pre: FY 2026 closed, balances final
1. CHIEF POST /roll-year {from: 2026, to: 2027} → new DRAFT batch with copied rows
2. Prior-year fix → re-roll refreshes (old batch superseded, audit kept)
Exc: target year not OPEN → 409; missing close → 422
```

## UC-08 — TT200→TT99 conversion map (alternative)

```
1. CHIEF uploads map {old_code → new_code} per TT99 Điều 23 (138→2281, 338-div→332, 441+466→4118...)
2. System rewrites GL rows + revalidates regime codes
3. Reconcile re-run before lock
```

## Exception matrix

| Condition | Code | HTTP |
|---|---|---|
| missing actor/reason | ValueError | 422 |
| batch not DRAFT on post | BATCH_LOCKED | 409 |
| unbalanced at lock | UNBALANCED_OPENING | 409 |
| Nợ and Có both >0 | INVALID_BALANCE_LINE | 422 |
| unknown/inactive master | NOT_FOUND / INACTIVE | 404/422 |
| cross-company FK | COMPANY_MISMATCH | 422 |
| AUDITOR write | SOD_VIOLATION | 403 |
| unauthenticated | UNAUTHENTICATED | 401 |
| live voucher before lock | NO_OPENING_LOCK | 409 |

## State machine

```
Batch:  [∅] ─create→ DRAFT ─lock→ LOCKED ─reopen(CHIEF)→ DRAFT ─lock→ LOCKED
Rows:   add/edit/delete only in DRAFT. LOCKED immutable (vouchers only).
```

## Mock policy (tests)

- Unit: FakeRepo fakes for ports; domain pure asserts.
- Integration: real `create_app(TESTING=True)` + seeded FY/COA/masters (follow `test_inventory_api.seeded` pattern).
- Excel: build `.xlsx` in-memory (openpyxl) — no fixture files.
