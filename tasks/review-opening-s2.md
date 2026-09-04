# Review Opening S2 — Counterparty AR/AP + aging hook

## Context
- Second vertical slice: per-party opening balances with proof flags, subledger=GL tie enforced at lock, locked-opening rows feed ledger AR aging. S1 fakes updated (new repo method).

## Correctness
- [x] Party validated same-company + active via injected `party_lookup`; unknown → 404, cross-company/inactive → 422
- [x] Side constrained debit/credit, amount > 0 at domain; proof flag stored per row (≥5tr AP path ready)
- [x] Lock now also verifies R-O03 tie per account (±0.01); S1 paths unaffected (no counterparty rows → no-op)
- [x] Aging hook adds only 131/1311 locked rows as current; non-AR accounts ignored; empty hook when unwired
- [x] Tests: 5 unit RED→GREEN + 1 integration (tie + aging current=200.0); full suite 1077 passed (1071 + 6)

## Readability
- [x] One domain entity, one service method, one web endpoint; tie-check helper named by rule id

## Architecture
- [x] Ports only (`party_lookup` callable, `opening_balances` callable into ledger); no storage imports cross-brick; ledger default unchanged when unwired
- [x] Late-bound party lookup in app (party wires after opening) with graceful None
- [x] Migration `d4e5f6a7b8c9` guarded; scratch up/down/re-up green, single head

## Security
- [x] AUDITOR 403 (shared `_require_write`); tenant match enforced server-side; no secrets

## Performance
- [x] Tie check loops batch rows only (small); aging adds one batch scan; no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (136 files)
- [x] `pytest -q` 1077 passed

## Verdict
- [x] **Approve** — merge Opening S2.
