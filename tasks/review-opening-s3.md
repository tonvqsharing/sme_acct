# Review Opening S3 — Stock opening by SKU×warehouse

## Context
- Third vertical slice: per-SKU opening rows materialized as DONE moves (no GL — opening GL covers), SKU=GL tie at lock, FIFO receipt-detail rule. Product link FKs from Slice 4 reused for account resolution.

## Correctness
- [x] Rows validate product/location same-company + active, qty > 0, value ≥ 0; FIFO/specific need receipt_date + unit_cost
- [x] Unit derived value/qty when receipt price absent; materialized moves feed NXT/costing day one (integration proves in_qty 100.0)
- [x] R-O02 tie groups by category account; products without category/account skipped (documented); mismatch names account + amounts
- [x] Tests: 5 unit RED→GREEN + 1 integration (tie-block + NXT); full suite 1083 passed (1077 + 6)

## Readability
- [x] One domain entity, one service method, one endpoint; tie helper named by rule id; no clever code

## Architecture
- [x] Stock math stays in inventory brick (`post_opening_move`, no FY gate/GL — opening GL covers); opening service orchestrates via injected port
- [x] Late-bound inventory holder in app breaks the build-order cycle with comment; voucher/invoice order untouched
- [x] Migration `e5f6a7b8c9d0` guarded; scratch up/down/re-up green, single head

## Security
- [x] Tenant match on product/location; AUDITOR 403 via shared guard; no secrets

## Performance
- [x] Tie check loops batch rows only; materialize one move per row; no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (136 files)
- [x] `pytest -q` 1083 passed

## Verdict
- [x] **Approve** — merge Opening S3.
