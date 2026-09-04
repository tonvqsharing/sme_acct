# Review — Opening S4a (FA + bank tie)

Verdict: **Approve.**

## Scope
- `AssetOpening` rows (`kind=fixed_asset`, NG/GTCL/months_left/expense account) + table `opening_assets` + repo + `POST /api/v1/opening-batches/<bid>/assets`.
- Materialize FA at go-live with prior depreciation carried over (`accumulated = NG − GTCL`); no GL from assets (opening GL covers).
- Lock ties: bank detail ↔ GL 112x (`_verify_bank_tie`), FA GTCL ↔ GL 211−214 net (`_verify_asset_tie`, R-O04).
- `FixedAssetService.create_asset` gains optional `accumulated_depreciation` (default 0, validated within `[0, NG]`) — backward compatible.

## Assumptions (documented)
- Useful life unknown from book state: effective life = `max(useful_life_months input, months_left)`; SL never over-charges; book value exact via carried accumulated.
- WIP 154 covered by GL trial tie (no project master this version); CCDC backfill deferred to S4b — endpoint rejects `kind != fixed_asset` with 422.
- Build order: `_LateFixedAssets` resolves FA service at call time (same pattern as inventory).

## TDD
- RED `tests/unit/opening_balance/test_assets.py` (4 tests: materialize+accumulated, remaining≤NG guard, bank tie, FA tie) → GREEN.
- Integration `TestAssetFlow`: POST assets materializes FA (acc 400M, BV 800M), wrong 211/214 net blocks lock with "211".
- S1 integration updated: bid2 GL uses 1121 so bank tie passes (old 1111+bank row now correctly rejected).

## Gates
- `ruff` 0, `black` 0, `mypy` 136 files 0.
- `pytest -q`: **1088 passed** (1083 + 4 unit + 1 integration).
- Migration `f6a7b8c9d0e1` guarded, scratch up/down/re-up green, single head.

## vs ERP parity
- MISA opening TSCĐ (NG/HM lũy kế/tháng còn lại) + đối chiếu 211/214: covered.
- MISA bank tie 112x: covered.
