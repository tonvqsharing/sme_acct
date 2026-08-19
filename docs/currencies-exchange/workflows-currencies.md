# Workflows — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-08-19 |

## W-1 Exchange rate lifecycle (state machine)

```
          ┌──────────┐  validate   ┌──────────┐  insert   ┌──────────────┐
          │ DRAFT    │ ──────────► │ ACTIVE   │ ────────► │ SUPERSEDED   │
          │ (form)   │             │ (stored) │           │ (history)    │
          └──────────┘             └────┬─────┘           └──────────────┘
                                        │ referenced by posted txn
                                        ▼
                                 ┌──────────────┐
                                 │ LOCKED       │  (immutable — RateLockedError)
                                 └──────────────┘
```

- DRAFT → ACTIVE: validation passed (D2).
- ACTIVE → SUPERSEDED: newer rate row for same (currency, type, date) inserted; old row retained (D3).
- ACTIVE → LOCKED: referenced by posted transaction; cannot delete/change.
- No transitions out of LOCKED (forward-fix + revaluation only).

## W-2 Revaluation run (approval workflow)

```
ACCOUNTANT                      CHIEF ACCOUNTANT
    │ create draft (UC-06)            │
    ▼                                 │
DRAFT ───────────────────────────────►│
    │                                 │
    │            review + approve ────┤
    │                                 ▼
    │                            PENDING_APPROVAL ──► APPROVED (approve)
    │                                 │
    │                                 │  post (UC-06 step 5)
    │                                 ▼
    │                                POSTED
    │                                 │
    │              reverse (UC-07) ───┤
    │                                 ▼
    │                                REVERSED
```

Transitions:
- DRAFT → PENDING_APPROVAL (auto on create with differences)
- PENDING_APPROVAL → APPROVED (CHIEF_ACCOUNTANT)
- APPROVED → POSTED (CHIEF_ACCOUNTANT; postings balanced, D6)
- POSTED → REVERSED (CHIEF_ACCOUNTANT, reason required; blocked if period locked without force)
- REVERSED → DRAFT (re-run, idempotent D7)
- Any → DRAFT: reject by creator (if not yet posted)
- POSTED → (re-run same period): reverse then re-apply (idempotent)

Guards:
- POST/PREPARE blocked when period locked (D8).
- POST blocked without APPROVED (D9).
- Postings must balance tol 0.01 (D6).

## W-3 Currency status

```
INACTIVE ──► ACTIVE ──► (in use) ──► cannot deactivate (E1/E2)
                ▲
                └── reactivate (admin)
```

- ACTIVE: selectable in transactions.
- INACTIVE: hidden from new transactions; history retained.
- Deactivate blocked when referenced (UC-02 E1) or base (E2).

## W-4 Approval flow for config changes (CONFIG-type)

Mirrors system-settings 2nd-approval pattern:
- CONFIG change requested → PENDING → CHIEF_ACCOUNTANT approves → APPLIED → audit-logged.
- LAW-type → FlagLockedError immediately (no workflow).