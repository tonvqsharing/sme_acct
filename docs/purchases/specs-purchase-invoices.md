# Specs — Purchase Invoices Module (Hóa đơn mua vào)

_Version 1.0.0 · Compiled 2026-08-24 · Legal base verified against mof.gov.vn / vbpl.vn mirrors as of 2026-08_
_Framework: Luật QLT 108/2025 → **NĐ 254/2026/NĐ-CP** + **TT 91/2026/TT-BTC** (eff 01/07/2026, replacing NĐ 123/2020+70/2025 and TT 32/2025) · Input-VAT: Luật GTGT 2024 Đ.14 + NĐ 181/2025 Đ.26 (sửa NĐ 144/2026)_

---

## 1. Brick position

```
src/bricks/purchases/
├── contract.py      # SupplierInvoiceRepositoryPort (primitives only)
├── domain.py        # SupplierInvoice, SupplierInvoiceLine + statuses + exceptions
├── services.py      # PurchaseService
├── storage.py       # supplier_invoices table + adapter
└── web_adapter.py   # purchases_bp
```

Depends on: `company` (tenant), `fiscal_year_period` (posting gate), `coa` (regime-aware posting gate), `payment_terms` (numbering PT→PC not required; purchase docs use own `PMUA` series optional), `bank_cash` (payment linkage later).

## 2. Data model — `supplier_invoices`

| Field | Type | Rules |
|---|---|---|
| id | UUID PK | |
| company_id | UUID, INDEX | tenant isolation |
| supplier_name | VARCHAR(255) | denormalized from supplier master (brick pending) |
| supplier_mst | VARCHAR(14) | MST format `^[0-9]{10}(-[0-9]{3})?$` when present |
| invoice_number | VARCHAR(30) | seller's số hóa đơn |
| invoice_symbol | VARCHAR(30) | ký hiệu |
| invoice_date | DATE | per NĐ 254 Art. timing rules (goods: transfer of ownership; services: completion; nightly tx: next business day) |
| entry_date | DATE | posting date — must fall in OPEN period (FY gate) |
| lines | JSON | see line schema below |
| subtotal | NUMERIC(18,2) | pre-VAT goods value |
| vat_deductible | NUMERIC(18,2) | Σ deductible input VAT (1331-bound lines) |
| vat_non_deductible | NUMERIC(18,2) | non-deductible VAT capitalized into cost |
| total_payment | NUMERIC(18,2) | subtotal + all VAT |
| payment_method | ENUM(cash/bank/none) | drives non-cash-proof requirement |
| payment_proof | BOOLEAN | non-cash proof present? (Điều 26 NĐ 181) |
| deductibility | ENUM(DEDUCTIBLE/PENDING_PROOF/NON_DEDUCTIBLE) | derived rule R-4 |
| status | ENUM(DRAFT/POSTED/CANCELLED) | soft-cancel only (10-yr retention) |
| checksum | CHAR(64) | SHA-256 chain per audit-log rules |
| created_at / created_by / cancelled_* | | actor discipline (D11) |

**Unique:** `(company_id, supplier_mst, invoice_number, invoice_symbol)` — duplicate ingestion guard (mirrors MISA/Fast "hóa đơn trùng").

### Line schema

```json
{
  "expense_account": "6421",          // or 152/156/211… regime-aware detail code
  "description": "Văn phòng phẩm T8",
  "amount_pre_vat": "2000000",
  "vat_rate": "0.1",                  // 0 / 0.05 / 0.08 / 0.1 per TaxRate config
  "vat_amount": "200000",
  "deductible": true                  // false ⇒ VAT capitalizes into expense_account
}
```

## 3. Domain invariants

- `subtotal = Σ amount_pre_vat`; `vat_amount = round(amount_pre_vat × rate)` per line
- `total_payment = subtotal + Σ vat_amount`
- `vat_deductible = Σ vat_amount where deductible ∧ proof-satisfied`
- CANCELLED rows immutable except cancel metadata; never deleted (R-6 retention)

## 4. Contract port

```python
class SupplierInvoiceRepositoryPort(ABC):
    def create(inv) -> inv
    def get_by_id(id) -> inv | None
    def get_by_company(cid) -> list[inv]
    def exists_duplicate(cid, mst, number, symbol) -> bool
    def update(inv) -> inv
```

## 5. Service — `PurchaseService`

Methods: `create_invoice` (gates below), `get`, `list(company, status?, deductibility?)`,
`post(id, actor, reason)` DRAFT→POSTED with checksum+audit event,
`cancel(id, actor, reason)` POSTED→CANCELLED (SOD-lite: CHIEF+ roles),
`validate_before_entry(company_id, id)`.

**Gate order (matches house convention):**
1. FY period open for `entry_date`
2. every `expense_account` ACTIVE posting-level under company regime
3. duplicate key check
4. totals recompute & match payload

**Deductibility engine (R-4):**
- DEDUCTIBLE ⇔ invoice is VAT invoice ∧ line marked deductible ∧ (total_payment < 5,000,000 ∨ payment_proof)
- ≥5M without non-cash proof ⇒ PENDING_PROOF (still posts; excluded from VAT declaration until proof attached)
- Non-VAT invoices/agricultural-from-household ⇒ NON_DEDUCTIBLE (VAT=0)

## 6. API (`purchases_bp`)

| Method | Path | Roles |
|---|---|---|
| GET | `/api/v1/purchase-invoices` | READ_ROLES (incl AUDITOR) |
| GET | `/api/v1/purchase-invoices/<id>` | READ_ROLES |
| POST | `/api/v1/purchase-invoices` | WRITE_ROLES |
| POST | `/api/v1/purchase-invoices/<id>/post` | WRITE_ROLES |
| POST | `/api/v1/purchase-invoices/<id>/cancel` | CHIEF_ACCOUNTANT, ADMIN |

Error codes: `EX-P01 MISSING_ACTOR(400)` · `P02 DUPLICATE_INVOICE(409)` · `P03 PERIOD_CLOSED(409)` · `P04 INVALID_ACCOUNT(422)` · `P05 TOTAL_MISMATCH(422)` · `P06 ALREADY_POSTED(409)` · `P07 NOT_POSTED_ON_CANCEL(422)` · `AUDITOR_READ_ONLY(403)`.

## 7. Out of scope v1 (explicit)

XML auto-ingest from TCT portal/email (needs TT91 annex field mapping + vendor API contract); supplier master brick; inventory receipt generation (phiếu nhập kho); import-duty VAT (nhập khẩu). Each gets its own spec session.
