# Data Flows — Sales

## DF-S01 Create draft invoice

```
HTTP POST /api/v1/invoices
  {company_id, template_code, invoice_symbol, issue_date, customer_mst,
   items:[{account_code, description, amount, vat_rate, category, qty?}], currency_code?, fx_rate?, reason, actor}
       │
       ▼
InvoiceService.create_invoice
  ├─ require actor+reason
  ├─ fy.find_open_period(company_id, issue_date)  ──► 409 if None
  ├─ for each item:
  │    ├─ vat_rate fraction ∈ allowed?  ──► 422 INVALID_VAT_RATE
  │    ├─ rate_gate(fraction, issue_date) covers? ──► 422 VAT_RATE_EXPIRED/SOON
  │    └─ vat=0.08? is_8pct_eligible(category)?  ──► 422 VAT_CATEGORY_INELIGIBLE
  ├─ coa.validate_posting_account(company_id, code, regime) ──► 422
  ├─ numbering.issue(company_id, symbol) → "HD/000001"  (8-digit, year-scoped per NĐ254)
  ├─ terms.get_default? → due_date = issue_date+due_days
  ├─ Invoice(...) + vat_breakdown derived + checksum(GENESIS, actor, reason)
  └─ repo.save → 201 {number, subtotal, vat_breakdown, grand_total, due_date}
       │
       └──► audit.append(entity_type=invoice, action=CREATE)
```

## DF-S02 Post + auto-journal

```
POST /invoices/<id>/post {reason, actor}
  │
  ▼
repo.get_by_id → 404 if miss → 409 if already POSTED
  ├─ fy.find_open_period still OPEN?  (re-check)
  ├─ on_posted(voucher, actor, chief_approved) — cash balances BEFORE status flip  (keeps DRAFT on failure)
  ├─ status→POSTED, checksum(prev, actor, reason), repo.save
  ├─ AutoJournal.lines_from_invoice(inv, codes=resolve_chart_role regime)
  │     { Nợ 131 grand_total, Có 511 subtotal, Có 3331 vat_amount (or per-breakdown lines) }
  └─ VoucherService.create+post (same gates: fy, coa, balanced) → PT/000001 POSTED
       │
       ├──► audit.append(invoice POST) + (voucher POST)
       └──► response 200 {status:POSTED, voucher_id, voucher_number}
```

## DF-S03 E-invoice issue (NĐ254)

```
POST /invoices/<id>/einvoice/issue
  ├─ invoice must be POSTED + einvoice_status==NOT_ISSUED
  ├─ validate template_code (ký hiệu mẫu số) + symbol + số HĐ sequence (max 99,999,999/yr/ký hiệu)
  ├─ render XML (Phụ lục NĐ254: tên HĐ, ký hiệu, thông tin bên bán/mua, dòng hàng, thuế suất, tổng)
  ├─ sign (CA) → envelope {invoice_id, xml, status=SIGNED}
  ├─ send GDT (thuedientu.gdt.gov.vn) → SENT | REJECTED (4xx → HOLD)
  └─ persist envelope + update invoice.einvoice_status → audit ISSUE
```

## DF-S04 Ledger read-model (posted-only)

```
GET /reports/general-journal?company_id&from&to&page
  LedgerService.general_journal
    source.get_posted_lines(company_id, start, end)  // SQLAlchemyLedgerSource — filters status=POSTED
      → group by entry_date|number → sorted chronological → paginate

GET /reports/trial-balance?company_id&from&to
  LedgerService.trial_balance
    source.get_posted_lines(...)
      → Σ debit/credit per account_code → sorted → totals.debit==totals.credit
```

ASCII pipeline:

```
[FY+COA+TaxRateWindow] ──┐
     Numbering (HD/PT) ──┼──► InvoiceService.create (gates) ──► DRAFT ──► post ──► Voucher (PT/)
     Terms (due_days)  ──┘                                 └─► audit_log
                                                                     │
                                                              ┌──────┴──────┐
                                                              ▼             ▼
                                                     SQLAlchemyLedgerSource  VAT output (01/GTGT)
                                                              │             │
                                                              ▼             ▼
                                                        general_journal  trial_balance
                                                        (POSTED only)    (POSTED only)
```

## DF-S05 Sales deduction (521)

```
POST /invoices/<id>/deduction {type, amount, reason}
  ├─ source invoice POSTED?
  ├─ amount ≤ source subtotal?
  └─ create voucher lines: Nợ 5211/5212/5213 / Có 131  (or Nợ 511 reversal per TT99)
      → VoucherService gated → POSTED → ledger now nets revenue
```

## Persistence contract (primitives across seams)

```
InvoiceService  ◄──►  fy: {find_open_period(UUID, date) -> Period|None}
                 ◄──►  coa: {validate_posting_account(UUID, str, regime)}
                 ◄──►  numbering: {issue(UUID) -> str}
                 ◄──►  terms: {get_default(UUID), get_payment_term(UUID)}
                 ◄──►  audit: {append(entity_type, entity_id, action, actor_id, reason, after_value)}
                 ◄──►  rate_gate: (fraction:str, on:date)-> True | raises ValueError

LedgerService ◄──►  source: {get_posted_lines(company_id, start, end) -> Iterable[{voucher_id, number, entry_date, description, account_code, debit, credit}]}
No cross-brick SQLAlchemy joins — all via contract primitives (AGENTS.md brick boundaries).
```

