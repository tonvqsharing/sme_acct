# Review — Opening S4b (CCDC backfill + 242 tie)

Verdict: **Approve.**

## Scope
- `ToolEquipmentService.open_ccdc_with_history(...)`: create CCDC + backfill
  `elapsed = life − months_left` POSTED allocation rows walked forward from
  purchase month; final row absorbs VND rounding so rows sum exactly to
  `price − remaining`. History rows bypass FY-open gate (predate go-live).
- Opening `post_assets` routes `kind=ccdc` to ccdc port (late-bound `_LateCCDC`,
  same pattern as FA/inventory); FA branch unchanged.
- Lock tie split R-O04: FA remaining ↔ GL 211−214, CCDC remaining ↔ GL 242
  (each enforced when either side nonzero); reconcile exposes
  `fa_total/ccdc_total/gl_242`.
- No migration: CCDC rows reuse `opening_assets` (`kind=ccdc`).

## Domain constraints honored (found via RED)
- CCDC expense account must be aggregate (`627`, not `6273`); COA
  posting-detail check applies to FA branch only — CCDC service validates
  aggregate allowlist + `is_account_active` itself.
- Multi-period CCDC requires `prepaid_account_code="242"` — backfill sets it.

## TDD
- RED `tests/unit/tools_equipment/test_opening_backfill.py` (3 tests: 5 elapsed
  rows sum 5M POSTED, remaining guard, full-remaining no rows) → GREEN.
- RED `tests/unit/opening_balance/test_ccdc.py` (2 tests: port routing, 242 tie)
  → GREEN.
- Integration `TestCCDCFlow`: POST assets kind=ccdc → 201, wrong 242 net
  blocks lock with "242".

## Gates
- `ruff` 0, `black` 0, `mypy` 136 files 0.
- `pytest -q`: **1094 passed** (1088 + 6).

## vs ERP parity
- MISA opening CCDC (NG/GTCL/tháng còn lại → kỳ phân bổ còn lại) + đối chiếu
  242: covered. WIP 154 stays GL-trial covered (no project master).
