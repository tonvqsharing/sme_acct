# Processes · Rules · Data Flows · Workflows — Fixed Assets

## 1. Monthly depreciation workflow

```
START (month-end)
│
├─→ POST /depreciation-runs/compute {company_id, year, month}
│   │
│   ├─ Gate 1: FY period open for month
│   ├─ Query: all ACTIVE assets WHERE accumulated < original_cost
│   │
│   ├─ Per asset:
│   │   monthly = NG / useful_life_months
│   │   capped_at_remaining = min(monthly, NG − accumulated)
│   │
│   ├─ Group by depreciation_account → build voucher lines
│   ├─ Create + post voucher: Dr {expense} / Cr 214
│   ├─ Update each asset.accumulated_depreciation += amount
│   └─ Return summary {count, total}
│
└─→ END (idempotent: re-run skips fully-depreciated assets)
```

## 2. Asset lifecycle

```
CREATE ──▶ ACTIVE ──depreciate──▶ ACTIVE ──...──▶ ACTIVE (fully depreciated)
                    │                                │
                    └── deactivate ──▶ CLOSED         └── deactivate ──▶ CLOSED
```

CLOSED is terminal; no un-close path in v1.

## 3. Rules Summary

| ID | Rule | Enforced by |
|---|---|---|
| R-FA1 | original_cost > 0 | Entity |
| R-FA2 | useful_life_months ≥ 1 | Entity |
| R-FA3 | unique (company, asset_code) per company | Service + repo |
| R-FA4 | depreciate only when ACTIVE and accumulated < cost | Service.compute_and_post |
| R-FA5 | monthly capped at remaining (NG − accumulated) | Service.compute_and_post |
| R-FA6 | soft-deactivate only; CLOSED blocks compute | Service.deactivate_asset |
| R-FA7 | SHA-256 checksum chain on every mutation | _stamp pattern |

## 4. Data flow

```
[Vendor] →(Hóa đơn TSCĐ)→ Purchases brick → voucher POSTED
                                    ↓
FixedAsset.create ← (manually entered or auto-created from purchase line)

Monthly: DepreciationService → voucher (Dr expense/Cr 214) → ledger
                                                          → trial balance
```

## 5. Integration points

| Brick | Direction | Content |
|---|---|---|
| fiscal_year_period | reads | find_open_period(month) |
| coa | reads | validate_posting_account(depreciation_account, regime) |
| voucher | writes | depreciation journal via create_voucher + post_voucher |
| audit_log | writes | CREATE / DEPRECIATE / CLOSE events |
