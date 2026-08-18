# Fiscal Years & Accounting Periods Module — Workflows

## 1. Period lifecycle state machine

```
                close (request+approve)
   ┌──────────┐ ───────────────────────────► ┌──────────┐
   │   OPEN   │                              │  LOCKED  │
   │ (accept  │ ◄─────────────────────────── │ (blocked)│
   │ entries) │   reopen (approve+reason)    └──────────┘
   └──────────┘                                    │
        │                                     year-end close
        │                                   (all periods locked)
        │                                         ▼
        │                                  ┌──────────┐
        └─────────────────────────────────►│YEAR_CLOSED│
                      (no direct           └──────────┘
                       OPEN→YEAR_CLOSED)
```

Transitions:

| From | To | Trigger | Rules |
|---|---|---|---|
| OPEN | LOCKED | close request + approval | SOD R-07; optional force for open drafts (A2 in UC-04) |
| LOCKED | OPEN | reopen + approval | reason mandatory (UC-06); approver ≠ requester |
| OPEN | YEAR_CLOSED | year-end close | NOT allowed directly — R-08 requires all LOCKED |
| LOCKED | YEAR_CLOSED | year-end close | all periods locked + no unposted (UC-07) |
| YEAR_CLOSED | (any) | — | forbidden; corrections via current period (R-10) |

## 2. Fiscal year lifecycle

```
CREATE (12 months, quarter-aligned) ─► ACTIVE (periods OPEN)
        │                                    │
        │ first period ≤ 15 months           │ change fiscal year (UC-08)
        ▼                                    ▼
   FIRST_PERIOD ──────────────────► TRANSITION ──► ACTIVE (new year_code)
        │                                    │
        └───────────────────► CLOSED ◄───────┘
                             (YEAR_CLOSED, opening
                              balances posted)
```

## 3. Close-period approval workflow (SOD)

```
[accountant] POST /periods/<id>/close {reason}
      │ 201 {"status":"PENDING_APPROVAL"}
      ▼
[ke_toan_truong] POST /periods/<id>/lock-events {approval_ref, decision}
      │ approver == requester? ── YES ──► 403 SelfApprovalError
      │ NO
      ├── APPROVE ──► status = LOCKED; event persisted (checksum)
      └── REJECT ──► stays OPEN; event REJECTED logged
```

- Every transition emits `PeriodLockEvent` (append-only, SHA-256 chain — audit
  parity with audit-log module).
- UI shows pending approvals; AUDITOR sees read-only history.

## 4. Year-end close pipeline (UC-07)

```
preconditions (all periods LOCKED, no drafts)
        │ fail ──► 409 YearEndPreconditionsError (lists offenders)
        ▼
kết chuyển generation: doanh thu/chi phí → 911 → 421
   (TT99; Tryton/Odoo P&L appropriation parity)
        │
        ▼
opening balances computed per account (Số đầu năm)
        │
        ▼
create next fiscal year + 12 OPEN periods
        │
        ▼
post opening balance entry into new year period 1 (KCS ledger)
        │
        ▼
FY status = YEAR_CLOSED; report + summary returned
```

## 5. Change-of-fiscal-year workflow (UC-08)

```
validate current FY closable (A2.1)
        ▼
close current books (all periods LOCKED)
        ▼
snapshot transition BCTC (TT133 Đ.73 / TT99 transition)
        ▼
create new FY (quarter-aligned) + periods
        ▼
opening balances → "Số đầu năm" (A4)
        ▼
tax-notification checklist + notice template (templates/)
```

## 6. Posting enforcement sequence (UC-05)

```
[any entry mutation: Voucher.post, Invoice, Revaluation, FX import]
        │
        ▼
PeriodLockService.validate_before_entry(company_id, date, actor)
        │
        ├── period OPEN ──► proceed (entry posted)
        └── period LOCKED/YEAR_CLOSED ──► 409 PeriodLockedError
```

This MUST sit in the service layer (R-13); UI banner is informational only.

## 7. Scheduled enhancements (out of v1)

- Auto-lock (MISA "khóa sổ tự động" parity): cron at configured date closes
  periods past end_date with no open entries.
- Auto year-end at configured date (UC-07 A1).
