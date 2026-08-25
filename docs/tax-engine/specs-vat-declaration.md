# Mini-Spec — VAT Declaration Engine (Tờ khai 01/GTGT data feed)

_Version 0.1 · 2026-08-24 · Feeds the monthly/quarterly VAT return; the filing
XML itself stays out of scope until TT 91 annex mapping is verified._

## 1. Sources of truth (POSTED data only)

| Side | Source | Filter |
|---|---|---|
| Output (đầu ra) | Posted voucher lines, COA code starts with `333` (VAT payable family) | `entry_date` in period; amount = credit − debit |
| Input (đầu vào) | Purchase invoices, `status == POSTED`, `deductibility == DEDUCTIBLE` | `entry_date` in period; amount = `vat_deductible` |

Rationale: sales side already journals VAT through auto-vouchers
(Dr 131 / Cr 511 / Cr 3331); purchase side stores deductible split at
ingestion (deductibility engine R-P4/P5).

## 2. Formula

```
output_vat        = Σ(credit − debit) over 333* lines, period
input_deductible  = Σ purchases.vat_deductible, period, DEDUCTIBLE only
payable           = max(0, output_vat − input_deductible)
carry_forward     = max(0, input_deductible − output_vat)
```

`PENDING_PROOF` invoices are **excluded** until proof attached
(they flip to DEDUCTIBLE via PROOF_ATTACHED event, then appear).
`NON_DEDUCTIBLE` VAT is capitalized into expense — never declared here.

## 3. Period semantics

v1: calendar month (`year`, `month`). Quarterly election per company is a
future wrapper that sums its months — no schema impact.

## 4. Service contract

```python
class VatDeclarationService:
    def __init__(self, *, output_source, input_source): ...
    def declare(self, company_id: UUID, year: int, month: int) -> dict:
        # returns primitives-only dict (see §5)
```

Ports are plain callables injected at composition root:

- `output_source(company_id, start, end) -> list[line_dict]`
  (reuse `SQLAlchemyLedgerSource.get_posted_lines`)
- `input_source(company_id, start, end) -> list[inv_dict]`
  (adapter over supplier-invoice repo; primitives only)

## 5. Response shape

```json
{
  "period": {"year": 2026, "month": 8},
  "output_vat": 5500000.0,
  "input_vat_deductible": 200000.0,
  "vat_payable": 5300000.0,
  "carry_forward": 0.0,
  "detail": {
    "output_lines_count": 3,
    "input_invoices_count": 1,
    "pending_proof_excluded": 0
  }
}
```

## 6. API

| Method | Path | Roles |
|---|---|---|
| GET | `/api/v1/reports/vat-declaration?company_id&year&month` | READ_ROLES (AUDITOR OK) |

Errors: 422 invalid params; 401 unauthenticated.

## 7. Rules summary

| ID | Rule |
|---|---|
| R-V1 | POSTED documents only — DRAFT never aggregates |
| R-V2 | PENDING_PROOF excluded from input until proof attached |
| R-V3 | NON_DEDUCTIBLE VAT excluded (capitalized) |
| R-V4 | Payable floors at zero; excess input carries forward |
| R-V5 | Read-only: no mutation paths exist on this service |

---

## Addendum — Quarterly election

Companies electing quarterly GTGT filing (per Luật QLT 108/2025) aggregate
three consecutive months. The endpoint accepts `period_type=monthly|quarterly`
with `year`+`month` (monthly) or `year`+`quarter` (quarterly, 1-4).

Quarterly = sum of the three constituent monthly declarations. No new tables;
pure aggregation over existing monthly computation.
