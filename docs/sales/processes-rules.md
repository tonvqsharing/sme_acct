# Processes & Rules — Sales

## Processes

### P-S01 Create → Post → Journal

```
Actor                InvoiceService              COA/FY/Numbering/Terms      VoucherService        Ledger     Audit
  │ POST /invoices ───────────►│                              │                     │               │       │
  │                            ├─ fy.find_open_period ───────►│                     │               │       │
  │                            ├─ vat catalog+window+8% ─────►│                     │               │       │
  │                            ├─ coa.validate each line ────►│                     │               │       │
  │                            ├─ numbering.issue(HD/) ──────►│                     │               │       │
  │                            ├─ terms.due_date ────────────►│                     │               │       │
  │                            ├─ checksum+save DRAFT ◄───────┤                     │               │append │
  │◄── 201 {HD/..} ────────────┤                              │                     │               │       │
  │ POST /post ───────────────►│                              │                     │               │       │
  │                            ├─ on_posted(cash before flip)─┼────────────────────►│               │       │
  │                            ├─ status POSTED+checksum ─────┼─ save POSTED ──────►│               │append │
  │                            └─ AutoJournal.lines_from ─────┼─ create+post PT/ ──►│ get_posted (*)│append │
```

### P-S02 Revenue recognition (TT99)

1. Tag each `InvoiceItem.po_id` — if single PO → immediate 511. If multiple → allocate `grand_total` by standalone price.
2. Service POs → credit 3387 (doanh thu chưa thực hiện), schedule recognition job over service period.
3. Agent lane (`is_agent`) → net: only commission hits 511; gross routed to liability 338.
4. BĐS (`category=real_estate`) → hold in 338 until handover/control transfer evidence.

### P-S03 E-invoice issuance (NĐ254)

```
POSTED invoice → POST /einvoice/issue → validate ký hiệu mẫu số/số HĐ sequence (8 digits/year/ký hiệu, 1→99,999,999)
→ render XML per Phụ lục NĐ254 Art.10 → sign (CA) → persist envelope → enqueue send GDT → status SENT
→ retry/backoff on GDT 5xx; 4xx → HOLD for correction; 10y retention.
```

### P-S04 Sales deductions (521)

```
Source POSTED invoice → POST /deduction {type, amount, reason}
→ validate amount ≤ source subtotal → create voucher Nợ 521x / Có 131 → post (chief gate if >threshold)
→ ledger reflects net revenue; B02 provision excludes deductions already booked.
```

### P-S05 Period close guard

Before any POST: `fy.find_open_period` must return OPEN **and** `system_settings.period_lock.is_locked(company,fy,period)==false`. Close → 409.

## Rules (R-Sxx) — testable

| ID | Rule | Enforce | Test |
|---|---|---|---|
| R-S01 | Every POST checks FY OPEN on `issue_date` | service | `test_closed_period_blocked` |
| R-S02 | Every line `vat_rate` ∈ catalog; gate by `issue_date` window | service | `test_rate_sunset` |
| R-S03 | `0.08` only if `is_8pct_eligible(category)` on ALL lines | service | 9-cat UT |
| R-S04 | Every line account ACTIVE detail under company regime (TT99 vs TT133) | coa | `test_bad_account_rejected` |
| R-S05 | Voucher \|Σdebit-Σcredit\| ≤0.01 | voucher | `test_unbalanced_422` |
| R-S06 | Invoice checksum = sha256(prev \| id \| actor \| status \| canonical_items \| reason) | domain | `test_checksum_changes_on_item` |
| R-S07 | Number `số HĐ` sequential, 8 digits, per-year per-ký hiệu, max 99,999,999 | numbering | UT sequence |
| R-S08 | Ledger reads only POSTED | source | `test_draft_not_in_journal` |
| R-S09 | AUDITOR cannot POST/ISSUE/DEDUCT | web_adapter | `test_auditor_403` |
| R-S10 | Agent lane records net commission only | service | `test_agent_net` |
| R-S11 | BĐS revenue only on control transfer | service | `test_bds_defer` |
| R-S12 | Period lock blocks POST | fy+settings | `test_period_locked_409` |

## ASCII workflow (full)

```
                        ┌─────────────┐
                        │ Create FY   │
                        │ + COA +     │
                        │ Series HD/PT│
                        └──────┬──────┘
                               ▼
                    ┌──────────────────┐     validator chain
  Accountant ──────►│ POST /invoices   ├────► fy OPEN?
                    │ items× vat_rate  │      ├─ catalog+window?
                    │ category? FX?    │      ├─ 8% eligible?
                    └────────┬─────────┘      └─ coa ACTIVE detail?
                             │ 201 DRAFT              │
                             ▼                        ▼
                    ┌──────────────────┐     numbering HD/000001
                    │ DRAFT invoice    │◄──── due_date via terms
                    │ checksum GENESIS │      audit CREATE
                    └────────┬─────────┘
                             │ POST /post
                             ▼
                    ┌──────────────────┐      sso? cash on_posted before flip
                    │ POSTED invoice   │─────► Voucher PT/ Nợ 131 / Có 511+3331
                    │ + voucher POSTED │      checksum(prev) + audit POST
                    └────────┬─────────┘
                             ├─► E-invoice issue (NĐ254)
                             │   XML+sign → GDT SENT
                             ├─► Deductions 521 (if any)
                             │   Nợ 521 / Có 131
                             ▼
                    ┌──────────────────┐
                    │ Ledger (POSTED   │  general_journal (grouped, paginated)
                    │        only)     │  trial_balance (debit==credit)
                    │ → 01/GTGT output │  10y retention
                    └──────────────────┘
```

