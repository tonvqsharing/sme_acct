# Workflows — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

State machines, approvals, statuses.

---

## W-1 VAT rate change (LAW-type flag workflow)

```
Admin ──(request migration/change)──►
    │
    │  LAW-type flag: vat_rates
    │
    ▼
  ┌─────────────────────────────────────┐
  │  Migration not yet applied?          │
  │  ──────────────────────────────────►│  Yes │
  │  │  FlagLockedError: "Cơ quan quy định │
  │  │  là hằng pháp lý, không thể thay đổi │
  │  │  mà không có bản vá migration."     │
  │  └──────────────────────────────────┘
  │                       │
  │                       ▼  No
  │               Migration applied?
  │                   ──────────────────►│  Yes │
  │                                   │  2nd approval
  │                                   │    (CHIEF_ACCOUNTANT)
  │                                   │    ──────────────────►│  Approved
  │                                   │                       ▼
  │                                   │               Config change applied
  │                                   │                       ▼
  │                                   │               audit_logged
  │                                   │                       □
  │                                   └────No───────────►│  Reject
  │                                                     ▼
  │                                                    │  Requester notified
  │                                                     □
  └────No───────────────────────►│  FlagLockedError immediately
                                    (no workflow)
```

Transitions:
- Request → FlagLockedError if LAW-type + no migration (immediate, no workflow)
- If migration applied: Request → 2nd approval (CHIEF_ACCOUNTANT) → Applied → Audit‑logged
- Any → Reject → Requester notified

Guards:
- POST/PATCH blocked when LAW flag + no migration (immediate error)
- POST/PATCH requires 2nd approval when CONFIG-type + migration applied
- All mutations audit‑logged

---

## W-2 E-invoice series add (CONFIG-type 2nd-approval workflow)

```
CHIEF_ACCOUNTANT
    │
    │  Request: POST /api/v1/system_settings/e-invoice-series
    │       {prefix, ca_signer, actor}
    │
    ▼
  ┌─────────────────────────────────────┐
  │  First approval recorded (ADMIN or   │
  │   CHIEF_ACCOUNTANT)                  │
  │  ──────────────────────────────────►│
  │                                     │
  │  CHIEF_ACCOUNTANT approves?          │
  │  ──────────────────────────────────►│  Yes │
  │                                     │
  │  │  Applied: series activated          │
  │  │  ──────────────────────────────────►│
  │                                     │
  │  │  Reject: series not activated       │
  │  │  ──────────────────────────────────►│
  │                                     │
  └────No──────────────────────────────┘
```

Transitions:
- Request → First approval recorded
- First approval → CHIEF_ACCOUNTANT approves → Series activated + config_version++
- First approval → CHIEF_ACCOUNTANT rejects → Series not activated; requester notified
- Any → Series not activated without approval

Guards:
- POST requires actor UUID
- Second approval by CHIEF_ACCOUNTANT mandatory (CONFIG-type pattern)
- Series count max 15 (validated before approval)
- All steps audit‑logged

---

## W-3 Invoice VAT post (rate freeze workflow)

```
Accountant ──────────────────────────────────►│  Create Invoice + items
    │  (select vat_rate ∈ {VAT_0, VAT_5, VAT_10})
    │                                           │
    │                                           ▼
    │                           Draft invoice
    │                                           │
    │                                           ▼
    │                Chief Accountant approves?──┤
    │                ──────────────────────────┤
    │                                              │
    │              Yes ──────────────────────────────┤
    │                                              │
    │              ▼  Post invoice ──────────────────┤
    │                                             │
    │    Rate frozen: vat_rate + vat_amount +     │
    │    config_version at post time stored        │
    │    immutably; any change requires reverse    │
    │    (P-04 reverse pattern) + re-apply.        │
    │                                              │
    └────No─────────────────────────────────────────┘
    │
    ▼  Invoice stays DRAFT; caller routes to manager
```

Transitions:
- Draft → Posted (CHIEF_ACCOUNTANT approves + post)
- Posted → Rate frozen (vat_rate, vat_amount, config_version immutable)
- Posted → (reverse) → DRAFT (if need to change rates)
- Any → DRAFT: reject by creator (if not yet posted)

Guards:
- POST blocked in locked period (period_locks integration, per system-settings)
- POST blocked without APPROVED status (D9 pattern from revaluation)
- Postings must balance tol 0.01 (D6)
- Rate frozen after post; change requires reverse + re-apply

---

## W-4 VAT review (Auditor read‑only workflow)

```
Auditor ──────────────────────────────────────►│  Open Tax Config → Tax Rates view
                                              │
                                              ▼
                                     │  Display: vat_rates frozenset,
                                     │  rate change history, config changes
                                     │  with actor + timestamp + reason
                                     │
                                     ▼
                              │  Filter invoices by VAT rate, period, company
                              │
                              ▼
                       │  Show per-invoice: serial, VAT rate/item,
                              │  VAT amount, total, frozen rate ref.
                              │
                              ▼
                       │  Export report (CSV/PDF); read‑only
                              │
                              □
```

Transitions:
- Open view → Filter → Export → Exit
- No transitions that modify data (read‑only)

Guards:
- AUDITOR role constant: read-only
- All GET endpoints respect RBAC; POST/PATCH/PUT → 403
- Audit log always writable; readable by all roles