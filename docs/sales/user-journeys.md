# User Journeys — Sales

## J-S01 Accountant sells goods (VND, single PO, 10% VAT) — happy

```
1. Opens FY 2026 (Jan-Dec MONTHLY, all OPEN) + COA 511/131/3331 + HD/ PT/ series.
2. Creates invoice: KH "Cty A", MST 0101234567, issue 2026-08-10,
   items: [{5111 10tr, 0.1}, {5111 5tr, 0.1}]? Actually current single-rate: header 0.1
   → system derives subtotal 15tr, vat 1.5tr, grand 16.5tr, due 2026-09-09 (Net30).
3. Reviews 201 draft HD/000001.
4. Clicks Post → system re-checks OPEN, posts voucher PT/000001 Nợ 131 16.5tr / Có 511 15tr + Có 3331 1.5tr.
5. Checks Ledger: general_journal shows HD/000001 PT/ chronological; trial_balance 131 net +16.5tr.
6. Month-end: VAT output aggregates into 01/GTGT (cross-read via carry repo).
```

## J-S02 Mixed-rate sale (5% + 10% + 8% allowed)

```
1. Invoice: teaching books (5%), consulting (10%), eligible manufacturing (8% in window, category ok).
2. System computes vat_breakdown per line → total 2.9tr on 35tr.
3. Posts → voucher expands to multiple Có 3331 lines (or single summed per code but breakdown persisted).
```

## J-S03 Sale with bundle (TT99 multi-PO)

```
1. Contract: máy + bảo trì 12 tháng. Items tagged po_id=GOODS vs SERVICE.
2. System allocates price by standalone selling price: 70% → immediate 511, 30% → 3387 deferred.
3. Monthly job recognizes 1/12 of deferred → Nợ 3387 / Có 511 over 12 months. Ledger shows deferred liability until recognized.
```

## J-S04 Agent sale (marketplace)

```
1. Item marked is_agent=true, gross 100tr but commission 5tr.
2. System: voucher Nợ 131 5.5tr / Có 511(commission) 5tr + Có 3331 0.5tr — gross 100tr never hits 511.
3. Auditor verifies agent note disclosure in financial_statements (B01 note).
```

## J-S05 E-invoice issue (NĐ254)

```
1. After POSTED, Chief clicks "Phát hành HĐĐT".
2. System renders XML với ký hiệu mẫu số 1C26TAA, ký hiệu HD/000001, số HĐ 8 digits.
3. Ký số CA → gửi GDT → status SENT → KH receives PDF+XML. Sequence locked; duplicate barred.
```

## J-S06 Sales return / deduction (521)

```
1. Customer returns half goods. Chief creates deduction RETURN amount 7.5tr (≤ subtotal).
2. System auto voucher: Nợ 5211 7.5tr + Nợ 3331 0.75tr / Có 131 8.25tr (if return includes VAT).
3. Trial balance net revenue adjusted; B02 provision excludes deduction amount.
```

## J-S07 Period closed — frustrated path

```
1. Accountant tries POST on 2026-08-10 but FY closed Aug (period CLOSED via fy.close_period).
2. System returns 409 NO_OPEN_PERIOD "Kỳ sổ chưa mở cho ngày hạch toán".
3. Must reopen via PeriodCloseService (only CHIEF) or move issue_date to OPEN period.
```

## J-S08 Auditor read-only journey

```
1. Auditor logs in (role AUDITOR).
2. Can GET /invoices, GET /reports/general-journal, GET /reports/trial-balance → 200.
3. Tries POST /invoices → 403 SOD_VIOLATION (web_adapter role guard).
4. Exports ledger CSV for audit file (10y retention satisfied via audit_log chain).
```

## Journey map ASCII

```
[Setup] FY+COA+Series  →  [Draft] create (gates)  →  [Post] journalize  →  [Issue] HĐĐT (NĐ254)
        │                          │ 8% gate                  │ cash-before-flip     │ sign+send GDT
        └───────────►  period lock / coa / vat window checks ─┴──────────► ledger ───┴──► BCTC notes
                                      │ exception: 422/409             │ deductions 521 ──► net revenue
                                      ▼                                ▼
                                 Auditor read                      VAT 01/GTGT output
```

