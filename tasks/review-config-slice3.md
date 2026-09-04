# Review Config Slice 3 — E-invoice flag + variance account decision

## Context
- Closes the two deferred follow-ups: e-invoice issuance gated by panel flag (PROD-safe default off), and Standard variance booking decided via panel account (empty = legacy single-line).

## Correctness
- [x] `sales_einvoice_enabled` bool flag default False; service port `einvoice_enabled_of` defaults allow (unit behavior); app wires panel; web maps 403 `E_INVOICE_DISABLED`
- [x] Existing issue tests opt in via panel PATCH (proves flag end-to-end) + new flag-off 403 test
- [x] `variance_account` flag default "" (= ride COGS line, legacy); when set and ≠ COGS with variance ≠ 0, balanced 3-line voucher (positive: Nợ variance/Có 152; negative mirrored); COA gate fail-closes on unknown account
- [x] Chart roles added (`inventory/cogs/ap` both regimes); old try/except fallbacks simplified to direct codes
- [x] Storage None-guards for pre-migration rows; migration `b2c3d4e5f6a7` guarded, scratch up/down/re-up green, single head
- [x] Tests: 3 flag unit + 1 variance unit RED→GREEN + 1 integration flag-off; full suite 1062 passed (1057 + 5)

## Readability
- [x] Variance validator collapsed to single elif (SIM102-clean, no noqa); ports mirror `threshold_of`/`exclusion_of` style

## Architecture
- [x] Domain pure (flag fields with safe defaults); ports cross the seam (no storage imports); wiring order kept (panel block before invoice)
- [x] No new tables; additive columns only; additive audit keys untouched

## Security
- [x] Flag PATCH keeps role gate + version conflicts; issue keeps CHIEF/ADMIN SOD plus flag 403; tenant isolation on variance port (per-company config)

## Performance
- [x] One config read per issue/post (same pattern as threshold); no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (130 files)
- [x] `pytest -q` 1062 passed

## Verdict
- [x] **Approve** — merge Config Slice 3.
