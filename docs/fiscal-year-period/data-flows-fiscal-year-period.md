# Fiscal Years & Accounting Periods Module — Data Flows

## DF-1 Posting-time lock check (hot path)

```
Client (UI/API)
   │ POST /api/vouchers | /api/invoices | revaluation run | FX import
   ▼
[Route] @casbin_required(roles)
   ▼
[Service layer]  VoucherService.post / InvoiceService / RevaluationService
   │
   ▼
PeriodLockService.validate_before_entry(company_id, entry_date, actor)
   │   cache lookup (60s TTL, per company+date)
   ├── miss ──► PeriodLockRepositoryPort.is_locked()
   │              │  SQL: SELECT 1 FROM accounting_periods
   │              │       WHERE company.fiscal_years AND
   │              │             start_date <= :d AND end_date >= :d
   │              │             AND status != 'OPEN'  LIMIT 1
   │              └──► cached
   ├── locked ──► raise PeriodLockedError(period_id, label)
   │                 └──► 409 {"error":"PERIOD_LOCKED","period_id":...,"message":"..."}
   └── open ──► proceed with entry persistence (transaction)
```

**Data written**: voucher/invoice rows + audit-log entry (actor, date, doc ref).

## DF-2 Close period (lock)

```
[accountant] POST /periods/<id>/close {reason}
   ▼
[Service] close_period(period_id, actor, reason)
   │  1. load period (SELECT ... FOR UPDATE)
   │  2. require status == OPEN (else 409)
   │  3. check open-draft prerequisites (warn/force path)
   ▼
[Repo] lock(): UPDATE accounting_periods SET status='LOCKED',
               locked_by, locked_at, lock_reason WHERE id=... AND status='OPEN'
   │  (0 rows affected → concurrent race → 409)
   ▼
[Repo] insert PeriodLockEvent(action=CLOSE, requester, approver=NULL,
                              reason, checksum)
   │
   ▼
[AuditLogService] append (checksum chain)
   ▼
[Cache] invalidate (company, all dates in period range)
   ▼
201 {period_id, status: LOCKED}
```

## DF-3 Year-end close + carry-forward

```
[ke_toan_truong] POST /fiscal-years/<id>/close
   ▼
[Service] close_fiscal_year()
   │  preconditions: every period status == LOCKED (R-08)
   │                 no draft/unposted in range
   ▼
[Kết chuyển] generate journal entries: doanh thu/chi phí → 911 → 421
   │  write into current (locked) year — YEAR_CLOSED marker entries
   ▼
[Opening balances] SELECT account, SUM(debit)-SUM(credit) per account
   │                for FY range → OpeningBalancesResult
   ▼
[Create new FY] fiscal_years row (next year_code) + 12 accounting_periods OPEN
   │
   ▼
[Post opening entry] single balanced journal entry dated new-FY start
   │  (TK 111/112/131/…: Nợ/Có mirror of closing balances; "Số đầu năm")
   ▼
[Mark old FY] status = YEAR_CLOSED, closed_by/at
   ▼
[AuditLogService] append; invalidate caches
   ▼
200 {closing_summary, opening_balances_url, new_fiscal_year_id}
```

## DF-4 Change of fiscal year

```
[ke_toan_truong] POST /fiscal-years/change {new_period_type}
   ▼
[Service] change_fiscal_year()
   │  validate: new start quarter-aligned (R-01)
   │  require: current FY closable (all periods LOCKED) else 409
   ▼
[Transition snapshot] BCTC report of transition period (short period)
   │
   ▼
[Create new FY] quarter-aligned periods; opening balances → "Số đầu năm"
   │
   ▼
[Notify] tax-notification checklist + notice template (evidence ref recorded)
   │
   ▼
200 {new_fiscal_year, transition_report_url, notification_checklist}
```

## DF-5 Lock-event history / audit export

```
GET /fiscal-years/<id>/history
   ▼
[Repo] SELECT * FROM period_lock_events ORDER BY requested_at
   ▼
[Verify] recompute SHA-256 chain vs stored checksums
   ▼
200 {events: [...], chain_verified: bool}
```

## Data ownership

| Table | Owned by | Mutations |
|---|---|---|
| fiscal_years | FiscalYearService | create, close, change |
| accounting_periods | PeriodLockService | close, reopen |
| period_lock_events | PeriodLockService | append-only |
| vouchers/invoices/revaluation_runs | respective services | blocked by DF-1 |
| audit_log | AuditLogService | append-only |

## Notes
- Concurrency: row locks (`FOR UPDATE`) + conditional UPDATE guard on all
  status flips (NFR-2); unique constraints on (company, year_code) and
  (fiscal_year_id, period_number).
- All dates stored as `date`, boundary math in ICT; no DST in VN.
