# Data Flows — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-18 |

## DF-1 Rate import flow (CSV → DB)

```
[CSV file] ──► Upload (API /exchange-rates/import)
                  │ validate each row (code/date/type/rate)
                  ▼
             Valid rows ──► atomic insert ──► exchange_rates table
                  │                              │
                  └── invalid rows ──► error report (row n: msg)
                                                      │
                                                      ▼
                                             audit_log (actor, source=CSV_IMPORT)
```

## DF-2 NHNN sync flow (v1.5)

```
NHNN (sbv.gov.vn) ──► fetch central rates (source=NHNN)
        │ down? ──► 502, rates unchanged, manual fallback
        ▼
    upsert exchange_rates (rate_type=CENTRAL)
        ▼
    audit_log + sync report
```

## DF-3 Booking transaction flow

```
Invoice/Voucher (currency ≠ VND)
    │
    ▼
resolve_booking_rate(entry_side, currency, rate_date)
    ├── debit  → actual transaction rate (giao dịch thực tế)  [R1]
    ├── credit → weighted avg (bình quân gia quyền)           [R1]
    │              avg = Σ(orig × rate) / Σ(orig)
    └── none available → manual entry (audit-flagged) or 400
    ▼
store: currency_code, amount_original, amount_vnd, fx_rate, fx_rate_type
    ▼
rate → LOCKED (referenced)
    ▼
e-invoice: tỷ giá quy đổi (ND 254/2026)
```

## DF-4 Revaluation flow

```
period_end trigger (unlocked period)
    │
    ▼
collect monetary items (FX cash/bank/receivables/payables)
    │
    ▼
closing rate per item: tỷ giá mua bán chuyển khoản trung bình [R2]
    (demand deposits → bank of account)
    │
    ▼
compute new_vnd = balance_original × closing_rate
        diff = new_vnd − old_vnd
    │
    ▼
build balanced journal (gain→515, loss→635) or TK 413 per config [R3]
    │
    ▼
DRAFT → PENDING_APPROVAL → APPROVED → POSTED
    │
    ▼
update fx_differences rows (opening/movements/closing/adjustment)
    │
    ▼
audit_log (run id, actor, approver, timestamps)
```

## DF-5 Reporting flow

```
FX difference report query:
  fx_differences (company, period, currency, account)
      + revaluation_runs for traceability
      + exchange_rates history for rate audit
  ──► UI/CSV export (AUDITOR read-only)
```

## DF-6 Audit trail flow

```
any mutation (rate create, import, revaluation, config change)
    │
    ▼
audit_log entry: entity, entity_id, action, actor_id,
                 old_value, new_value, reason, timestamp
```

## Data ownership

| Data | Owned by | Written by | Read by |
|---|---|---|---|
| currencies | Admin | Admin | all |
| exchange_rates | Accountant | Accountant/Chief/import/sync | all |
| revaluation_runs/entries | Chief Acct | workflow (DRAFT→POSTED) | all (auditor read) |
| fx_differences | Chief Acct | revaluation service | all |
| FX config (CompanyConfig) | Chief Acct | Chief/Admin (2nd approval) | all |
| invoice/voucher FX fields | Accountant | booking service | all |

## External systems

| System | Direction | Purpose |
|---|---|---|
| NHNN sbv.gov.vn | inbound (v1.5) | central rates |
| e-tax (thuedientu.gdt.gov.vn) | outbound (future) | e-invoice FX data (ND 254/2026) |
| CSV files | inbound | rate import |