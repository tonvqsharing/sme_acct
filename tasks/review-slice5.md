# Review Slice 5 — Variance + costing split

## Context
- Extracts costing math from `InventoryService` into pure `costing.py`; books Standard variance into COGS line with audit split. No variance GL account exists yet.

## Correctness
- [x] Matches spec: `moving_average_unit` (fallback on zero stock), `specific_out_unit` (lot else standard), `fifo_out_unit` (oldest lot via replayed outs), `split_standard` (cogs +/− variance, VND quantized)
- [x] STANDARD out: COGS at standard, variance = (wavg actual − standard) × qty; `mv.unit_cost` stays standard so stock value tracks standard
- [x] Non-standard paths byte-identical behavior (wavg/fifo/specific delegate, same fallbacks)
- [x] Tests: 6 new (`test_costing.py`: 5 pure + 1 service variance with FakeVoucher/FakeAudit asserting debit 1,040,000 and audit split); full suite 1033 passed (1027 + 6)

## Readability
- [x] `costing.py` 60 lines pure, each method one function; service `_compute_out_cost` now 4 one-line dispatches; removed unused `deque` import
- [x] Known shortcoming: variance rides the same 6321 debit/1521 credit line, so GL 1521 drifts from standard-valued stock by exactly the variance — disclosed in audit `variance_total`, no silent hiding

## Architecture
- [x] Math in owning layer (`inventory/costing.py`), orchestration stays in service; no new cross-brick deps; voucher 2-line shape unchanged; audit `after_value` extended additively (`cogs_total`, `variance_total`)
- [x] Follow-up (separate, needs COA decision): dedicated variance account + `resolve_chart_role("variance")`; not bolted on here

## Security
- [x] No input-surface change; tenant isolation untouched; `@login_required`/SOD untouched; no secrets; SQLA params only

## Performance
- [x] Same query count as before (stock qty/value already fetched); FIFO replay unchanged complexity; no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (128 files)
- [x] `pytest -q` 1033 passed

## Verdict
- [x] **Approve** — merge Slice 5.
