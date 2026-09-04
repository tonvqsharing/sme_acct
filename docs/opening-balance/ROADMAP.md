# Roadmap & Execution Plan — Opening Balance to Full PROD

## Gantt (5 sprints, 2 weeks each)

```
W1-2   W3-4   W5-6   W7-8   W9-10
├──────┼──────┼──────┼──────┤
│ S1   │ S2   │ S3   │ S4   │ S5   │ hardening
│GL+   │AR/AP │Stock │FA/   │Excel │
│bank  │party │SKU   │CCDC  │gate  │
│      │      │      │WIP   │roll  │
```

## Sprint breakdown (tracer-bullet, smallest shippable first)

### S1 — GL + bank opening + lock gate (2w)

```
T1 domain: OpeningBatch(DRAFT/LOCKED) + GLBalance(single-side) + checksum
T2 service: create/post/reconcile-trial/lock/reopen + audit
T3 storage: 2 tables + repo
T4 web: 5 endpoints + AUDITOR 403 + voucher gate NO_OPENING_LOCK
T5 tests: UT domain+gates, integration GL→lock→voucher allowed
Verify: pytest -k opening, mypy, black — old 1062 still green.
```

### S2 — Counterparty AR/AP (1w)

```
T1 domain: CounterpartyBalance(party FK, side, proof flag)
T2 service: validate party same company; ≥5tr AP proof note
T3 AR/AP aging reads opening as_of FY.start
T4 tests: UT + integration tie R-O03
```

### S3 — Stock opening (2w, largest)

```
T1 domain: StockOpening(qty/value/lot/receipt detail)
T2 service: materialize DONE moves (unit=value/qty or receipt price)
T3 FIFO/specific receipt rows required fields
T4 reconcile SKU=152/153/155/156/157/158
T5 tests: UT + integration first-out-after-opening
```

### S4 — FA/CCDC/WIP + bank (2w)

```
T1 AssetOpening unified (kind/code/remaining/months)
T2 seed FA masters + depreciation from months_left; CCDC allocation same
T3 WIP 154 header (project text ref)
T4 BankOpening per bank master
T5 reconcile R-O04/R-O05 + tests
```

### S5 — Excel + gate + year-roll (2w)

```
T1 template download per group
T2 upload ≤10 .xlsx: header check, row validate, valid-only, error sheet, delete-reload
T3 go-live gate on voucher post (NO_OPENING_LOCK 409)
T4 roll-year close→open copy + refresh + TT200→TT99 map table
T5 tests: in-memory .xlsx (openpyxl), no fixture files
```

## Order rationale (why S1 first)

S1 is smallest slice proving batch lifecycle + trial gate + voucher integration. S2/S3 reuse batch. S4 needs stock pattern. S5 needs all groups + lock semantics.

## Execution checklist (per AGENTS.md gate)

```
Each PR:
  uv run ruff check src tests      → fix
  uv run black --check src tests   → fix
  uv run mypy --ignore-missing-imports src/bricks/<brick>  → fix
  uv run pytest -q                → 1062+ (increment)
  git add + commit Conventional (feat(opening-balance): ...)
```

## Risk & mitigation

| Risk | Mitigation |
|---|---|
| TT200→TT99 map wrong | Ship manual map table first, auto-mapper later; Điều 23 table in specs |
| Excel lib weight | openpyxl test-only; PROD parse via stdlib zip/xml read of .xlsx |
| FIFO opening cost wrong | Require receipt rows for FIFO/specific; WAVG accepts totals |
| Reopen abuse | CHIEF-only + reason + full audit; lock date recorded |
| Period interplay | Opening date = FY.start; pre-lock only opening batch posts |

## Done definition for full PROD

```
Full opening PROD = S1–S5 closed + SKU=GL + trial balanced enforced
                  + year-roll proven + Excel round-trip tested.
Feature flag opening.enabled → true.
Runbook + 10y chain test passed.
```
