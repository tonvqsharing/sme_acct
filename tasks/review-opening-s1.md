# Review Opening S1 — GL + bank + lock gate

## Context
- First vertical slice of opening brick: batch lifecycle, GL/bank rows, trial gate, voucher go-live guard. Stock/AR/FA/Excel/year-roll deferred to S2–S5.

## Correctness
- [x] Batch DRAFT→LOCKED, reopen CHIEF-only; locked posts rejected; unbalanced lock rejected with diff
- [x] GL single-side rule at domain; COA ACTIVE-detail gate per regime; FY belongs-to-company check
- [x] Voucher gate grandfathered (no batches → skip) so 1000+ existing tests unaffected; new batch without lock → 409 `NO_OPENING_LOCK`
- [x] Tests: 7 unit RED→GREEN + 2 integration (full flow incl. gate + AUDITOR read-only); full suite 1071 passed (1062 + 9)

## Readability
- [x] 5-file Lego; service 180 lines; web handlers mirror voucher style; no clever code

## Architecture
- [x] Domain pure; ports only (`fy_years.get_by_id`, `coa.validate`, `audit.append`); no cross-brick storage imports
- [x] Wiring order safe (opening before voucher); same `fy_session` repo shared, no new session
- [x] Migration `c3d4e5f6a7b8` guarded both lineages; scratch up/down/re-up green, single head

## Security
- [x] Actor+reason everywhere; AUDITOR 403 writes; lock CHIEF/ADMIN, reopen CHIEF; tenant match on FY; no secrets

## Performance
- [x] Reconcile sums in Python over batch rows (small by nature); no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (136 files)
- [x] `pytest -q` 1071 passed

## Verdict
- [x] **Approve** — merge Opening S1.
