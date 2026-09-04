# User Journeys — Opening Balance

## J-O01 New SME day one (happy, Excel path)

```
1. ADMIN creates company + FY 2026 + COA + masters (Party/UOM/products/warehouses/bank).
2. KT downloads templates GET /templates/<gl|counterparty|stock|assets|bank>.
3. KT fills 5 sheets from old books (500 SKUs, 80 partners).
4. KT creates batch + uploads → {imported: 580, errors: 4} → fixes 4 rows → delete-reload → re-upload → 584/584.
5. KT checks reconcile: all green except 152 (SKU total 2.1T vs GL 2.0T) → finds missed lot → fixes → green.
6. CHIEF locks → team posts first live voucher same day.
```

## J-O02 Manual entry small shop (happy)

```
1. 20 SKUs, 5 partners — KT keys rows directly via API/UI forms.
2. Reconcile green first try → CHIEF locks in 30 minutes.
```

## J-O03 Unbalanced start (frustrated path)

```
1. KT enters GL Nợ 5T, Có 4.8T (typo).
2. Lock attempt → 409 UNBALANCED_OPENING {diff: 200tr, lines:[...]}.
3. KT fixes line → lock succeeds. No silent bad start possible.
```

## J-O04 Locked batch needs fix (alternative)

```
1. Week later auditor finds missed AP 50tr.
2. ACCOUNTANT edit → 409 BATCH_LOCKED.
3. CHIEF reopens with reason → KT adds row → reconcile → re-lock. Full trail kept.
```

## J-O05 Year-roll (happy)

```
1. FY 2026 closed Dec. CHIEF rolls → FY 2027 DRAFT batch prefilled.
2. Feb fix to 2026 (late invoice) → re-roll refreshes 2027 opening, supersede audit.
```

## J-O06 TT200→TT99 conversion (alternative)

```
1. Old books on TT200 codes. CHIEF uploads map table (138→2281, 338-div→332...).
2. System rewrites + revalidates under TT99 catalog.
3. Reconcile green → lock. Điều 23 satisfied with evidence.
```

## J-O07 Auditor verification (read-only)

```
1. Auditor opens batch → sees every row + checksum chain + lock actor/reason.
2. Downloads reconcile report → ties to B01 "Số đầu năm" column.
3. No edit buttons (403 on attempt).
```

## Journey map ASCII

```
[Setup] Company/FY/COA/masters → [Enter] manual/Excel → [Check] reconcile → [Lock] CHIEF → [Live] vouchers → [Roll] next year
       │ missing master            │ row errors           │ unbalanced      │ reopen w/ reason │ 409 w/o lock  │ supersede audit
       ▼                           ▼                      ▼                 ▼                   ▼                 ▼
     404 + template              error sheet            409 + diff        trail kept         gate enforced    history kept
```
