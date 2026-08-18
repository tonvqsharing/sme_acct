# Processes — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-18 |

End-to-end business processes. Numbered steps; actors; systems; exit criteria.

---

## P-01 Currency master setup (initial)

**Trigger:** First use of FX in a company.

1. Admin creates currencies (UC-01) — ISO codes, symbols, decimals.
2. System creates base currency VND (default) — LAW flag, immutable.
3. Chief Accountant sets FX config via CompanyConfig (UC-10):
   - fx_rate_source, fx_revaluation_account, approval flags.
4. Accountant imports historical rates (UC-04) or enters manually (UC-03).
5. Exit: currencies active, config set, rates available for transaction date.

## P-02 Daily rate maintenance

**Trigger:** New business day / rate update.

1. Accountant checks NHNN or bank rate sheet.
2. Enters rates manually (UC-03) OR imports CSV (UC-04) OR (v1.5) syncs NHNN (UC-11).
3. System validates + audit-logs.
4. Exit: rates for all active FX currencies, types (buy/sell/transfer), date ≤ today.

## P-03 Booking a foreign-currency transaction

**Trigger:** FX invoice/payment/receipt.

1. Accountant opens invoice/voucher; selects currency.
2. System resolves booking rate (R1): debit=actual, credit=weighted avg.
3. Accountant verifies original + VND amounts; posts.
4. System freezes rate; e-invoice tỷ giá quy đổi captured (R5).
5. Exit: posted entry with currency, rate, dual amounts; rate locked.

## P-04 Period-end revaluation (monthly/quarterly/yearly)

**Trigger:** Period close (before locking).

1. Accountant runs draft revaluation (UC-06) for (period, rate date).
2. System computes monetary items + closing rates (R2) + differences.
3. Draft PENDING_APPROVAL.
4. Chief Accountant reviews + approves.
5. Chief Accountant posts → 515/635 (or 413) entries, balanced (D6).
6. FXDifference rows updated (UC-08 reportable).
7. Period locked (existing system-settings lock_period).
8. Exit: POSTED run, audit trail complete, period locked.

## P-05 Revaluation correction

**Trigger:** Error found in posted run.

1. Chief Accountant reverses run (UC-07) with reason.
2. Fixes rates/items.
3. Re-runs P-04.
4. Exit: REVERSED + new POSTED run; audit shows both.

## P-06 Rate error correction

**Trigger:** Wrong rate entered.

1. Accountant inserts corrected rate row (new date or replace) — D3 (no in-place edit).
2. If referenced by posted transaction → RateLockedError; only forward-fix + revaluation.
3. Audit shows old/new.
4. Exit: corrected rate; revaluation re-run if period open.

## P-07 Period-end reporting

**Trigger:** FS preparation.

1. Accountant runs FX difference report (UC-08).
2. Auditor reviews rate history + revaluations (UC-09).
3. Chief Accountant signs FS in VND (R7).
4. Exit: FX amounts reconciled, FS complete.

---

## Process dependencies

```
P-01 ──► P-02 ──► P-03 ──► P-04 ──► P-07
              ▲                    │
              └── P-05, P-06 ──────┘ (corrections)
```

## Actors per process

| Process | Admin | Accountant | Chief Acct | Auditor |
|---|---|---|---|---|
| P-01 | ✓ | ✓ | ✓ | — |
| P-02 | — | ✓ | ✓ | — |
| P-03 | — | ✓ | — | — |
| P-04 | — | ✓ (draft) | ✓ (approve/post) | — |
| P-05 | — | — | ✓ | — |
| P-06 | — | ✓ | ✓ | — |
| P-07 | — | ✓ | ✓ | ✓ (read) |