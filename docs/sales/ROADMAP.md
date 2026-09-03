# Roadmap & Execution Plan — Sales to Full PROD

## Gantt (sprints, 2 weeks each)

```
W1-2   W3-4   W5-6   W7-8   W9-10   W11
├──────┼──────┼──────┼──────┼───────┤
│ S1   │ S2   │ S3   │ S4   │ S5    │ hardening & GDT sandbox
│P0-03 │P0-04 │P0-01 │P0-02 │P1     │ docs + 10y retention drill
│VAT line+RBAC│521 │multi-PO+agent+BDS│NĐ254 e-invoice│FX+COGS+aging
```

## Sprint breakdown (tracer-bullet, smallest shippable slice first)

### S1 — P0-03 Line-level VAT + P0-05 RBAC (2w)

```
Tasks:
  T1 domain: InvoiceItem.vat_rate + vat_breakdown + checksum canonical
  T2 service: gate per-line catalog+window+8% (move from header to loop)
  T3 web: accept items[].vat_rate, return vat_breakdown; block AUDITOR post (403)
  T4 migration: items JSON add vat_rate fallback header rate for old rows
  T5 tests: UT mixed-rate, UT old-data fallback, integration 8% per-line
Verify: pytest -k invoice, mypy, black — 968+ tests still green, mixed-rate accepted.
```

### S2 — P0-04 Sales deductions 521 (1w, parallelizable after S1 T1)

```
T1 domain: SalesDeduction type (enum RETURN/DISCOUNT/REBATE)
T2 service: POST /deduction validates amount≤subtotal, maps 5211/5212/5213 per type
T3 voucher: reuse VoucherService gated path, chief gate if >threshold
T4 ledger: trial_balance nets deductions (net_debit math already)
T5 tests: UT deduction, integration deduction→ledger
```

### S3 — P0-01 TT99 multi-PO + agent + BĐS (3w, largest)

```
T1 model: PerformanceObligation {id, standalone_price, is_service, is_agent}
T2 service: unbundle allocation by SSP, emit 3387 deferred, net-only for agent
T3 BĐS: defer until control evidence flag; disclose note payload for B01
T4 scheduler: monthly recognition job Nợ 3387 / Có 511 (reuse AllocationEngine pattern)
T5 tests: UT unbundle, UT agent net, UT BĐS defer, e2e ledger reflect deferred
```

### S4 — P0-02 NĐ254 e-invoice (2w, reuse purchases GDT XML pattern)

```
T1 contract: EInvoiceEnvelope {invoice_id, template_code, symbol, number8, xml, status}
T2 service: build XML per Phụ lục NĐ254 Art.10, validate 8-digit seq (99,999,999/yr/ký hiệu)
T3 signing seam: inject signer (CA) — mock in tests, real CA in PROD
T4 GDT submit: queue + retry (like purchases export_gdt_xml), audit ISSUE
T5 tests: UT sequence cap, UT XML valid, integration mock GDT 200
Flag: sales.e_invoice_enabled=false until sandbox pass on th PopupMenu.gdt.gov.vn
```

### S5 — P1 hardening (2w)

```
T1 FX: invoice currency_code/fx_rate/amount_original → voucher FX lines
T2 COGS stub: emit 632 when is_goods sale (link stock brick seam, no join)
T3 checksum harden: hash canonical items+breakdown
T4 ledger: pagination + period_lock guard wired
T5 AR aging: due_date → aging buckets view (read-only)
```

## Implementation order rationale (why S1 first)

- S1 is smallest isolated change that unlocks legal correctness (mixed VAT is common). Proves tracer bullet through domain→service→web→storage.
- S2 reuses voucher line; S3 is domain-heavy so needs stable VAT foundation first.
- S4 depends on stable POSTED semantics (S1) but is I/O heavy (XML/sign/send) — do after core accounting correct.
- S5 is additive, no breaking.

## Execution checklist (per AGENTS.md quality gate)

```
Each PR:
  uv run ruff check src tests      → fix
  uv run black --check src tests   → fix
  uv run mypy --ignore-missing-imports src/bricks/<brick>  → fix
  uv run pytest -q                → 968+ (increment)
  git add + commit Conventional (feat(sales): ...)
```

## Risk & mitigation

| Risk | Mitigation |
|---|---|
| TT99 unbundling scope creep | Start with 2 POs only (goods+service); BĐS as flag |
| CA signing complexity | Seam inject; PROD uses licensed CA, TEST mock |
| GDT schema drift | Re-check TT91/2026 Phụ lục quarterly; pin XSD |
| 8% sunset 31/12/2026 missed | Already automated via rate_windows sunset; add cron alert 30d before |
| Period lock missed | Wire SystemSettings period_lock adapter already exists in currencies/financial_statements — reuse |

## Done definition for full PROD

```
Full sales PROD = P0-01..05 closed + GDT sandbox round-trip 200
                + ledger pagination + checksum hardening.
Feature flag sales.e_invoice_enabled → true.
Runbook + 10y retention test (audit chain immutable) passed.
```

