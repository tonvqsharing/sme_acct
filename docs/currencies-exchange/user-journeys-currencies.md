# User Journeys — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-08-19 |

Role-based journeys. Emotional/practical steps; exit criteria.

---

## UJ-01 Admin — set up currencies

1. Notices company will do export in USD.
2. Opens Settings → Currencies.
3. Creates USD, EUR, JPY (UC-01); VND already present (base).
4. Activates currencies.
5. Done: currency pickers show new options.

## UJ-02 Accountant — maintain daily rates

1. Morning: checks NHNN/bank rate sheet.
2. Opens Exchange Rates → enters USD buy/sell/transfer (UC-03) or CSV import (UC-04).
3. Sees validation pass, audit entry.
4. Done: rates current; booking works all day.

## UJ-03 Accountant — book USD sale invoice

1. Creates invoice for foreign customer (UC-05).
2. Selects USD; system auto-fills rate (actual for debit, weighted avg for credit).
3. Verifies VND equivalent; posts.
4. Done: invoice shows both currencies + tỷ giá quy đổi; e-invoice ready (ND 254/2026).

## UJ-04 Accountant + Chief — monthly revaluation

1. Month end: accountant runs draft revaluation (UC-06).
2. Sees draft differences by account/currency; sanity-checks big items.
3. Sends to Chief Accountant for approval.
4. Chief approves + posts; postings 515/635 balanced.
5. Done: FX gains/losses booked; FS ready.

## UJ-05 Chief — config FX policy

1. Chooses rate source (NHNN sync later), revaluation account (DIRECT vs 413).
2. Updates CompanyConfig (UC-10) — CONFIG-type, 2nd approval.
3. Done: policy enforced system-wide; audit trail.

## UJ-06 Auditor — review FX treatment

1. Opens FX difference report (UC-08) for period.
2. Opens rate history (UC-09); verifies actors, sources, timestamps.
3. Opens revaluation runs; verifies approval chain.
4. Done: audit opinion supported; no anomalies.

## UJ-07 Accountant — fix wrong rate

1. Discovers wrong rate entered.
2. Inserts corrected rate row (P-06); old rate locked if referenced.
3. Re-runs revaluation for affected period (P-05).
4. Done: books correct; audit shows both.

## UJ-08 Chief — handle locked period conflict

1. Accountant tries revaluation in locked period → PeriodLockedError.
2. Chief unlocks period (existing system-settings), revaluation runs, re-locks.
3. Done: no silent overrides; forced reverse requires documented reason.

---

## Journey map (roles × stages)

| Stage | Admin | Accountant | Chief Acct | Auditor |
|---|---|---|---|---|
| Setup | UJ-01 | — | UJ-05 | — |
| Daily ops | — | UJ-02, UJ-03 | — | — |
| Period end | — | UJ-04, UJ-07 | UJ-04, UJ-08 | — |
| Review | — | — | — | UJ-06 |

## Pain points addressed

- Rate hunting: system auto-resolves booking rate (R1) — no manual lookup.
- Approval discipline: revaluation needs CHIEF_ACCOUNTANT (D9) — no rogue postings.
- Auditability: every rate/run logged (BR-06) — auditor self-service.
- Lock safety: period lock blocks revaluation (D8) — no FS restatement by accident.