# Template — Exchange Rate Import CSV

Standard format for `POST /api/exchange-rates/import`.

## Columns

| Column | Required | Format | Example |
|---|---|---|---|
| rate_date | yes | YYYY-MM-DD | 2026-08-18 |
| currency | yes | ISO 4217 (^[A-Z]{3}$) | USD |
| rate_type | yes | BUY / SELL / TRANSFER / CENTRAL / BOOKING | TRANSFER |
| rate | yes | decimal > 0, ≤ 18 integer digits, ≤ 6 decimals | 24850.000000 |
| source | no | default CSV_IMPORT | CSV_IMPORT |
| note | no | free text | import aug 2026 |

## Sample

```csv
rate_date,currency,rate_type,rate,source,note
2026-08-18,USD,BUY,24700,CSV_IMPORT,monthly update
2026-08-18,USD,SELL,24900,CSV_IMPORT,monthly update
2026-08-18,USD,TRANSFER,24800,CSV_IMPORT,monthly update
2026-08-18,EUR,BUY,29100,CSV_IMPORT,monthly update
2026-08-18,EUR,SELL,29350,CSV_IMPORT,monthly update
2026-08-18,EUR,TRANSFER,29200,CSV_IMPORT,monthly update
2026-08-18,JPY,BUY,168.5,CSV_IMPORT,monthly update
2026-08-18,JPY,SELL,170.2,CSV_IMPORT,monthly update
2026-08-18,JPY,TRANSFER,169.0,CSV_IMPORT,monthly update
```

## Validation rules (per row)

1. rate_date parseable as date.
2. currency exists + active in currencies table.
3. rate_type in enum.
4. rate > 0, numeric.
5. Duplicate (currency, rate_date, rate_type) → row error (or upsert per config).

## Error response shape

```json
{
  "imported": 6,
  "errors": [
    {"row": 7, "error": "currency JPY not active"},
    {"row": 9, "error": "rate must be > 0"}
  ]
}
```

## Notes

- Default atomic: if any row invalid → no rows applied (fx_import_partial=false).
- All imported rows audit-logged (actor, source=CSV_IMPORT, count).