# Review — Opening S5 (gate hardening + Excel + year-roll)

Verdict: **Approve.**

## S5a — go-live gate hardening (`6295b51`)
- `is_locked`: True only when EVERY batch LOCKED (any DRAFT blocks; was any-LOCKED).
- `post_voucher` re-checks gate (reopen-after-draft hole closed).
- S1 integration updated: first batch fixed + locked (hardened gate needs all locked).
- Tests: 5 new RED→GREEN.

## S5b — Excel GL import (`4adbe18`)
- `POST gl/import` parses `.xlsx` (`account_code/debit/credit[, currency_code]`)
  via openpyxl (already vendored via `markitdown[all]`) → `post_gl` untouched.
- Parsing lives in web_adapter (Flask-only file); header/empty/file validated 422.
- Tests: 2 integration RED→GREEN (import→lock 200, bad header 422).

## S5c — year-roll (this commit)
- `rollover(batch, new_fy)` copies LOCKED rows (GL/bank/CP/stock/assets) with fresh
  UUIDs into new DRAFT batch; NO materialization re-run (masters already live).
- Guards: source must be LOCKED (else 409), new FY same company (else 404);
  endpoint chief-only like lock/reopen.
- Tests: 2 unit + 1 integration RED→GREEN (copy balanced, draft→409).

## Gates
- `ruff` 0, `black` 0, `mypy` 136 files 0.
- `pytest -q`: **1104 passed** (1094 + 5 gate + 2 excel + 3 rollover).
- No migration (no schema change S5).

## vs ERP parity
- MISA import Excel số dư + khóa kỳ + chuyển năm sau: covered core path.
- Remaining (nice): multi-sheet import (bank/CP/stock/assets tabs) — deferred,
  single GL sheet + API rows cover all classes.
