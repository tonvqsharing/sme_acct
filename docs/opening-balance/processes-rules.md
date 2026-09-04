# Processes & Rules — Opening Balance

## Processes

### P-O01 Create → Enter → Reconcile → Lock → Go-live

```
Accountant            OpeningService              FY/COA/Masters           Ledger/Audit
  │ POST /batches ───────────►│                              │                │
  │                            ├─ FY belongs to company ────►│                │
  │◄── 201 DRAFT ──────────────┤                              │                │
  │ POST /<id>/gl|stock|... ──►│ gates 1-6 ─────────────────►│                │
  │                            ├─ materialize moves/masters ─►│                │
  │                            │                              │              append │
  │ GET /<id>/reconcile ──────►│ R-O01..R-O05, no mutation    │                │
  │◄── report ─────────────────┤                              │                │
  │ (CHIEF) POST /<id>/lock ──►│ balanced? ─────────────────►│                │
  │◄── LOCKED ─────────────────┤                              │              append │
```

### P-O02 Excel import

```
Template download → fill (no rename sheets/cols, * required) → upload ≤10
→ header check → row validate (master exists? numeric? side single?)
→ valid rows persist, error sheet returned → fix → delete-reload → re-upload
```

### P-O03 Year-roll

```
FY N closed → POST /roll-year {N → N+1} → copy rows as new DRAFT
→ prior-year fix → re-roll refresh (supersede, audit kept, no silent overwrite)
```

### P-O04 TT200→TT99 conversion

```
Upload code map (Điều 23 table) → rewrite GL rows → regime revalidate
→ reconcile re-run → lock. 138→2281, 338-div→332, 441+466→4118, 2413→2414.
```

### P-O05 Period interplay (MISA parity)

```
Opening date = FY.start_date. Posting before lock: opening batch only.
After lock: live vouchers only. Reopen needs CHIEF + reason + audit.
```

## Rules (R-Oxx) — testable

| ID | Rule | Enforce | Test |
|---|---|---|---|
| R-O01 | Trial balanced ΣNợ = ΣCó ±0.01 at lock | service | `test_lock_unbalanced_409` |
| R-O02 | SKU totals = GL 152/153/155/156/157/158 | reconcile | `test_stock_gl_tie` |
| R-O03 | Party totals = GL 131/331/141/138/338 | reconcile | `test_party_gl_tie` |
| R-O04 | Bank totals = GL 112x | reconcile | `test_bank_gl_tie` |
| R-O05 | FA remaining tie 211−214; CCDC tie 242 | reconcile | `test_asset_tie` |
| R-O06 | Exactly one side > 0 per GL line | domain | `test_both_sides_422` |
| R-O07 | FIFO/specific rows need receipt date+doc+price | service | `test_fifo_needs_receipt_422` |
| R-O08 | LOCKED immutable; reopen CHIEF only | web | `test_locked_edit_409`, `test_reopen_chief_only` |
| R-O09 | Live voucher before lock → 409 | voucher gate | `test_no_opening_lock_409` |
| R-O10 | Cross-company FK rejected | service | `test_cross_company_422` |
| R-O11 | AUDITOR read-only | web | `test_auditor_403` |
| R-O12 | Checksum = sha256(prev\|id\|actor\|state\|canonical\|reason) | domain | `test_checksum_chain` |

## ASCII workflow (full)

```
                        ┌──────────────┐
                        │ Company+FY   │
                        │ +COA+masters │
                        └──────┬───────┘
                               ▼
                    ┌──────────────────┐     validator chain
  Accountant ──────►│ POST /batches    ├────► actor+reason?
                    │ DRAFT            │      ├─ FY belongs?
                    └────────┬─────────┘      └─ masters same company?
                             │ 201 DRAFT              │
                             ▼                        ▼
              ┌──────────────────────────┐   GL/counterparty/stock/
              │ gl | counterparties |    │   assets/bank rows
              │ stock | assets | bank    │   (Excel or manual)
              │ + materialize moves      │
              └────────────┬─────────────┘
                           │ GET /reconcile
                           ▼
              ┌──────────────────────────┐
              │ R-O01..R-O05 all green?  ├── NO → fix rows, re-run
              └────────────┬─────────────┘
                           │ YES ─ CHIEF lock
                           ▼
              ┌──────────────────────────┐
              │ LOCKED → live vouchers   │  10y audit chain root
              │ year-roll → next FY      │
              └──────────────────────────┘
```
