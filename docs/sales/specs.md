# Specs — Sales Bricks (Invoice / Voucher / Ledger)

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-09-03 |
| Brick layout | `src/bricks/<invoice|voucher|ledger>/` → `domain.py` (pure) + `services.py` (ports) + `storage.py` (SQLA) + `web_adapter.py` (Flask) |

## 1. Domain model (target v1 — delta from current)

### 1.1 Invoice (current → target diff)

```
CURRENT (gap)                      TARGET v1 (P0-03)
─────────────────────────          ───────────────────────────────
Invoice.vat_rate: Decimal          InvoiceItem.vat_rate: Decimal  ← per line
header single rate                 vat_breakdown: dict["0.05": Decimal, ...]
compute_checksum(grand_total)      compute_checksum(canonical_items + vat_breakdown + status)
no currency                        + currency_code, fx_rate, amount_original
no ký hiệu                         + template_code, form_symbol, invoice_symbol  (NĐ254)
                                   + einvoice_status: Enum[NOT_ISSUED, SIGNED, SENT, ACCEPTED]
```

```python
# target domain sketch — pure Python, no Flask/SQLA
@dataclass
class InvoiceItem:
    account_code: str          # must be ACTIVE detail per regime
    description: str
    amount: Decimal            # VND tax-exclusive (or amount_original if FX)
    vat_rate: Decimal          # fraction str: 0, 0.05, 0.08, 0.1, -1(KCT)
    category: str | None       # for 8% eligibility
    quantity: Decimal = Decimal(1)
    unit_price: Decimal | None = None

@dataclass
class Invoice:
    company_id: UUID
    template_code: str         # ký hiệu mẫu số  — e.g. 1C26TAA
    invoice_symbol: str        # ký hiệu HĐ    — e.g. HD/  (prefix of numbering series)
    number: str                # số HĐ 8 digits/year — PT/000001
    issue_date: date
    customer_name: str
    customer_mst: str | None   # TaxId  ^[1-9]\d{2}(-\d{3})?$
    items: list[InvoiceItem]
    currency_code: str = "VND"
    fx_rate: Decimal | None = None
    due_date: date | None = None
    status: InvoiceStatus = DRAFT
    einvoice_status: EInvoiceStatus = NOT_ISSUED
    checksum: str = ""
    # derived
    @property
    def subtotal(self) -> Decimal: ...
    @property
    def vat_breakdown(self) -> dict[str, Decimal]: ...  # fraction→vat sum
    @property
    def vat_amount(self) -> Decimal: ...                # Σ breakdown
    @property
    def grand_total(self) -> Decimal: ...
```

### 1.2 Voucher (existing — minimal change)

`JournalLine`: `debit XOR credit >0`, `account_code` validated. Add `CASH_FLOW` handling untouched.

New `SalesDeduction` type is a voucher with `account 5211/5212/5213` debit + `131` credit (reversal).

### 1.3 Error codes (stable API)

| Code | HTTP | When |
|---|---|---|
| `NO_OPEN_PERIOD` | 409 | FY period not OPEN |
| `INVALID_ACCOUNT` | 422 | UNKNOWN/AGGREGATE/INACTIVE or wrong regime |
| `INVALID_VAT_RATE` | 422 | catalog miss |
| `VAT_RATE_EXPIRED` | 422 | window sunset after 31/12/2026 etc. |
| `VAT_CATEGORY_INELIGIBLE` | 422 | 8% on excluded cat |
| `UNBALANCED_VOUCHER` | 422 | \|debit-credit\| >0.01 |
| `ALREADY_POSTED` | 409 | double post |
| `EINVOICE_SEQUENCE_EXHAUSTED` | 409 | 99,999,999 / year / ký hiệu |
| `SOD_VIOLATION` | 403 | AUDITOR write or self-post chief gate |

## 2. Service contracts (ports — primitives only)

```python
class InvoiceService:
    def create_invoice(*, company_id, template_code, invoice_symbol,
                       customer_name, customer_mst, issue_date,
                       items: list[dict], currency_code, fx_rate,
                       actor: UUID, reason: str) -> Invoice: ...

    def post_invoice(invoice_id, *, actor: UUID, reason: str,
                     chief_approved: bool = False) -> Invoice: ...

    def issue_einvoice(invoice_id, *, actor: UUID, reason: str) -> EInvoiceEnvelope: ...

class LedgerService:
    def general_journal(company_id, start, end, *, page, page_size) -> Page[JournalEntry]: ...
    def trial_balance(company_id, start, end) -> list[BalanceRow]: ...
```

Gates (order fixed — matches voucher):
```
1. actor+reason required
2. items non-empty
3. FY find_open_period(company_id, issue_date) != None
4. vat_rate ∈ allowed_fractions (TaxRate to_fraction)
   gate(fraction, issue_date) covers?  (sunset aware)
   if 0.08 → is_8pct_eligible(category) on EVERY line
5. for each item: coa.validate_posting_account(company_id, code, regime)  (ACTIVE+detail)
6. numbering.issue(company_id, template_code+symbol) → 8-digit sequence
7. terms → due_date
8. balance? (for voucher; invoice grand_total derived)
9. checksum = sha256(prev | id | actor | status | canonical_items | reason)
```

## 3. HTTP API (web_adapter.py — ONLY Flask file)

```
POST   /api/v1/invoices                 — create DRAFT
GET    /api/v1/invoices?company_id=     — list (any authenticated)
GET    /api/v1/invoices/<id>            — detail
POST   /api/v1/invoices/<id>/post       — DRAFT→POSTED (+ auto-journal voucher)
POST   /api/v1/invoices/<id>/einvoice/issue  — sign XML, send GDT (P0-02)
POST   /api/v1/invoices/<id>/deduction  — 521 reversing voucher
GET    /api/v1/reports/general-journal?company_id=&from=&to=&page=
GET    /api/v1/reports/trial-balance?company_id=&from=&to=
```

Auth: `@login_required` all; `AUDITOR` writes → 403.

## 4. Storage

```sql
invoices
  id CHAR(36) PK
  company_id CHAR(36) FK+IDX
  template_code VARCHAR(20)   -- ký hiệu mẫu số  (NĐ254)
  invoice_symbol VARCHAR(20)  -- ký hiệu HĐ      (HD/)
  number VARCHAR(30) IDX      -- HD/000001 (8 digits seeded)
  issue_date DATE
  due_date DATE nullable
  customer_name VARCHAR(200)
  customer_mst VARCHAR(14) nullable
  items JSON                    -- [{account_code, description, amount, vat_rate, category}]
  currency_code CHAR(3) default 'VND'
  fx_rate VARCHAR(20) nullable
  status VARCHAR(10) DRAFT/POSTED
  einvoice_status VARCHAR(20)
  checksum CHAR(64)

-- existing voucher/ledger tables unchanged
-- new: einvoice_envelopes (invoice_id FK, xml TEXT, status, sent_at)
```

## 5. TT99 revenue cases (P0-01)

| Case | Detection | Accounting |
|---|---|---|
| Single PO goods | one item group | `Nợ 131 / Có 511 + Có 3331` at POST |
| Multi-PO bundle (goods+maintenance) | items tagged `po_id` distinct | Unbundle: allocate `grand_total` by standalone price → `3387` deferred for service PO → recognize over period |
| Agent / commission | `is_agent=True` | Net only: `Nợ 131 / Có 511(commission) + 3331(on commission)` — gross excluded |
| Real estate (BĐS) | category `real_estate` | Defer until control/handover; no schedule revenue |

## 6. Non-functional

- Decimal: `Decimal` everywhere, VND `quantize(1)`.
- Type safety: `from __future__ import annotations`, `Mapped[...]`, `dict[str,Any]` (strict mypy).
- Pagination: ledger `page/page_size` default 50, max 200.
- Period lock: `SystemSettings.period_lock.is_locked(company_id, fy, period)` → 409 if locked.
- Audit: every POST→ `audit.append(entity_type=invoice, action=POST/ISSUE/DEDUCT)`.
