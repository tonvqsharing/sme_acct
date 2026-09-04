# Review Config Slice 2 — Threshold port + 8% exclusion table

## Context
- Wires Slice 1 flags into gates: purchases deductibility reads panel threshold; 8% exclusion list moves from frozenset to seeded per-company table. Static stays as default/seed — no behavior change unless panel edits.

## Correctness
- [x] Threshold stamped per-invoice at create (`non_cash_threshold` field, default 5tr); reads round-trip via storage (None-guard for pre-migration rows); later panel changes don't rewrite history — correct audit
- [x] Exclusion table seeded from NĐ174 set on first use; unknown/empty → eligible (static semantics kept); company-isolated
- [x] Gates delegate via `threshold_of`/`exclusion_of` ports defaulting to static; app wires panel-backed callables
- [x] Old-row compat: `Decimal(None)`-guard falls back to 5tr default
- [x] Tests: 2 threshold unit + 3 exclusion unit RED→GREEN + 1 invoice override unit + 1 exclusion CRUD integration; full suite 1057 passed (1050 + 7)

## Readability
- [x] Ports mirror existing `rate_gate`/`regime_of` callable style; `exclusions.py` 68 lines; kwarg-splat replaced with explicit post-construction stamp (mypy-clean)

## Architecture
- [x] Domain stays pure (field with const default); no cross-brick storage imports (callables cross the seam); settings service built before invoice per wiring order
- [x] Migration `a1b2c3d4e5f6` guarded both lineages; scratch up/down/re-up green, single head
- [x] Follow-up (separate): `sales.e_invoice_enabled` flag; variance GL account

## Security
- [x] Threshold/exclusion edits ride existing flag roles + version conflicts (threshold) and ADMIN gate (exclusions); AUDITOR 403 proven; tenant isolation on all new queries

## Performance
- [x] One config read per purchase create (already-loaded-row pattern like series cap); exclusion check one indexed query per 8% line (rare path)

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (130 files)
- [x] `pytest -q` 1057 passed

## Verdict
- [x] **Approve** — merge Config Slice 2.
