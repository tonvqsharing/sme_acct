# Use Cases — Sales Bricks

## Actors

```
Accountant (KT viên) ── creates draft, posts small invoices
Chief Accountant ────── posts material / 8% excluded, issues e-invoice, approves deductions
Auditor ─────────────── read-only ledger + invoices
System ──────────────── gates, numbering, due-date, auto-journal, checksum, audit
CQT / GDT ───────────── receives HĐĐT XML (NĐ254)
```

## UC-01 — Create Draft Invoice (happy)

```
Pre: FY 2026 OPEN on issue_date, COA 511/131/3331 ACTIVE detail, HD/ series exists
Flow:
  1. Accountant POST /api/v1/invoices {company_id, template_code, symbol, issue_date, mst, items[{code, amount, vat_rate, category}]}
  2. System: fy gate → vat catalog+window(+8% per-line) → coa each line → numbering issue → terms.due_date → checksum(GENESIS) → save DRAFT
  3. Return 201 {number: HD/000001, subtotal, vat_breakdown, grand_total, due_date, status:DRAFT}
Alt: FX → currency_code+fx_rate present → amount stored as VND (amount_original preserved) + vat on VND
```

## UC-02 — Post Invoice + Auto-Journal (happy)

```
Pre: invoice DRAFT, period still OPEN
Flow:
  1. Actor POST /invoices/<id>/post {reason}
  2. System: not already POSTED → on_posted? (cash balances before flip) → status→POSTED → checksum(prev, actor, reason)
     → AutoJournal: lines = [Nợ 131: grand_total, Có 511: subtotal, Có 3331: vat_amount (or per-breakdown)] → Voucher POSTED PT/...
     → audit.append(invoice POST + voucher POST)
  3. Return 200 {status:POSTED, voucher_id, voucher_number}
Alt (arena test): already POSTED → 409 ALREADY_POSTED, no duplicate voucher
Exc: period CLOSED between create and post → 409 NO_OPEN_PERIOD
Exc: AUDITOR call → 403 SOD_VIOLATION
```

## UC-03 — Mixed VAT Rates (happy — TARGET)

```
Items: [511@5% 10tr, 511@10% 20tr, 511@8% 5tr (category allowed, date in window)]
System: validates each vat_rate individually, window per line-date, 8% eligibility per line
Derived: vat_breakdown={"0.05":500k, "0.1":2M, "0.08":400k} → total vat 2.9M → grand 37.9M
Journal: still single 131 debit; credits split by revenue? (one 511 line) + multiple 3331? → voucher lines reflect breakdown
```

## UC-04 — 8% Rejection (exception)

```
Item category=telecom, vat_rate=0.08 → 422 VAT_CATEGORY_INELIGIBLE "không áp dụng cho nhóm telecom theo NĐ174/2025"
Item date=2027-01-05 vat=0.08 → 422 VAT_RATE_EXPIRED "đã hết hiệu lực từ 2026-12-31 theo NQ204+ND174"
Unknown fraction 0.07 → catalog 422 immediately (before window)
```

## UC-05 — E-Invoice Issue (NĐ254 lane — P0-02)

```
Pre: invoice POSTED, template_code + symbol valid, period OPEN, actor=CHIEF/ADMIN
Flow:
  1. POST /invoices/<id>/einvoice/issue {reason}
  2. System: einvoice_status NOT_ISSUED → build XML per Phụ lục NĐ254 (tên HĐ, ký hiệu mẫu số, ký hiệu HĐ, số HĐ 8 digits, NCC/KH, dòng hàng, thuế suất)
     → sign (CA) → persist envelope → send GDT (mock → SENT) → einvoice_status=SENT
  3. Audit ISSUE + checksum update
Exc: sequence exhausted 99,999,999/year/ký hiệu → 409 EINVOICE_SEQUENCE_EXHAUSTED
Exc: ACCOUNTANT tries issue → 403
```

## UC-06 — Sales Deduction 521 (happy)

```
Trigger: returned goods / price reduction / chiết khấu
Flow:
  1. POST /invoices/<id>/deduction {type: RETURN|DISCOUNT, amount, reason, chief_approved?}
  2. System: source invoice must be POSTED → create reversing voucher: Nợ 521x / Có 131 (or 511 reversal) → POSTED immediately if chief_approved else DRAFT for approval
  3. Ledger: deduction appears as negative revenue in trial_balance (net_debit math)
```

## UC-07 — Ledger Queries (happy)

```
GET /reports/general-journal?company_id=&from=&to=&page=1
  → posted-only, grouped by entry_date|number, sorted chronological, paginated
GET /reports/trial-balance?company_id=&from=&to=
  → Σ debit/credit/net_debit per account, totals.debit==totals.credit, includes deductions
Alt: unauth → 401; bad UUID/date → 422; AUDITOR allowed (read)
```

## UC-08 — FX Sale (happy — P1)

```
items amount_original=USD 1000, fx_rate=25400, currency_code=USD
System: VND amount = 25,400,000; vat on VND; FX fields persisted on invoice + journal lines (amount_original+fx_rate)
Ledger: shows VND; note disclosure via financial_statements brick
```

## Exception matrix

| Condition | Code | HTTP |
|---|---|---|
| missing actor/reason | ValueError | 422 |
| empty items | ValueError | 422 |
| NO_OPEN_PERIOD | NO_OPEN_PERIOD | 409 |
| invalid/aggregate/inactive account | INVALID_ACCOUNT | 422 |
| vat not in catalog | INVALID_VAT_RATE | 422 |
| 8% ineligible / expired | VAT_* | 422 |
| unbalanced (voucher) | UNBALANCED_VOUCHER | 422 |
| already POSTED | ALREADY_POSTED | 409 |
| negative bank balance (cash path) | NEGATIVE_BALANCE | 409 |
| unauthenticated | UNAUTHENTICATED | 401 |
| AUDITOR write | SOD_VIOLATION | 403 |
| pagination overflow | — | 200 empty page |

## State machine

```
Invoice:  [∅] ─create→ DRAFT ─post→ POSTED ─issue→ E-SENT ─deduction→ (voucher)
                          │         │
                          └────────→ (NO_TRANSITION back)
Voucher:  DRAFT ─post→ POSTED (immutable, feeds ledger)
```

## Mock policy (tests)

- Unit: hand-build minimal Flask app with `FakeUser(UserMixin)+_store` or inject fakes for `fy/coa/numbering/terms`.
- Integration: real `create_app(TESTING=True)` + `FakeUser` in `_store` + `session_transaction`.
- FY/COA/series must be seeded before invoice (see `test_invoice_api._setup_company` pattern).
