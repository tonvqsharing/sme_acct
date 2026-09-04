# REVIEW — Opening Balance Brick PROD Readiness (BA Lead 20y + Chief Accountant 20y)

| | |
|---|---|
| Module | Opening Balance — Số dư ban đầu (AR/AP/stock/WIP/FA/CCDC/bank/GL) |
| Date | 2026-09-04 |
| Reviewers | BA Lead 20y ERP/SME + Chief Accountant VACPA 20y + Legal Research (mof/vbpl/thuvienphapluat/MISA SME 2026) |
| Gate | ruff → black → mypy strict → pytest (1062 green, 0 opening tests) |
| Verdict | **NOT PROD — brick missing entirely** |

## 1. TL;DR

```
Opening Balance brick DOES NOT EXIST → CAN NOT operate PROD.
Fresh company starts at zero with no lawful way to enter history.
Every workaround (fake vouchers, direct DB edits) poisons audit chain.
```

| Track | Verdict | Reason |
|---|---|---|
| Per-object opening (131/331/141 by partner, 152 by SKU×warehouse, 154 by project, TSCĐ/CCDC/bank) | **NO** | No entity, no endpoints |
| Excel template import + row validation + re-import | **NO** | `document_conversion` does docs→MD only |
| Balance gate (Nợ = Có before go-live) | **NO** | Nothing to check against |
| Year-roll close→opening chain | **NO** | No close chain; second year breaks |
| TT200→TT99 conversion (Điều 23 TT99) | **NO** | No mapping tool |
| Two-book split (sổ quản trị / sổ tài chính) | **NO** | Single book only |

## 2. Repo evidence (codegraph sync 2026-09-04)

```
Grep opening|open_bal|so_du_dau|dau_ky → fragments only:
  bank_cash: CashAccount.opening_balance field (create-time only, no flow)
  financial_statements: opening_cash param, RetainedEarnings.opening_balance
  currencies: open_balance_provider hook (unused)
Missing: OpeningBalance entity, POST /opening-balances/*, NXT-vs-152 reconcile,
         341-by-contract, 242 allocation, consignment flags, FX opening.
Tests: 1062 passed, 0 opening. Coverage 0%.
```

## 3. Laws double-checked (2026-09-04) — outdated REMOVED

```
OUTDATED — DO NOT USE              ACTIVE — USE
─────────────────────────          ─────────────────────────────────────
TT200/2014/TT-BTC                  TT99/2025/TT-BTC (27/10/2025, FY≥01/01/2026)
TT133/2016 + TT132/2018 (SME)      TT58/2026/TT-BTC (SME/micro, eff 01/07/2026)
NĐ123/2020 + NĐ70/2025 + TT32/2025 NĐ254/2026 + TT91/2026 (HĐĐT 01/07/2026)
VAS 02 LIFO as equal option        VAS 02 + TT99: Standard Cost 4th method
```

Active drivers:

- **TT99 Điều 22–23**: chuyển đổi loại hình / chia tách → toàn bộ số dư cũ ghi nhận số dư đầu kỳ mới, cột "Số đầu năm"; Điều 23: remap 111/112/113/121/153/154/156/211/212/213 chi tiết, 138→2281 (BCC non-control), 2413→2414, 338 cổ tức→332, 441+466→4118.
- **TT99 Điều 30**: đổi chính sách kế toán → hồi tố / hồi tố đơn giản / phi hồi tố.
- **VAS 02**: HTK at original price (purchase+processing+direct), NRV if lower; methods specific/WAVG/FIFO (+Standard per TT99).
- **Luật Kế toán 88/2015 Art.11**: 10y retention — opening chain is audit root.
- **NĐ181/2025 Đ.26** (sửa NĐ144/2026): input VAT ≥5tr non-cash proof — opening AP must carry proof flags.
- Verified: thuvienphapluat.vn full text, helpsme.misa.vn SME2026 (updated 03/2026), MISA SME 2026 site (TT99-ready, 19 phân hệ, 200+ reports).

## 4. MISA SME 2026 parity (latest, active)

| Concern | MISA SME 2026 | Our repo |
|---|---|---|
| Opening hub tabs | `Nghiệp vụ/Nhập số dư ban đầu` 10 groups | none |
| AR/AP/141 by counterparty | 131/331/141/138/338 detail | Party masters exist, no balances |
| Stock by SKU×warehouse×lot/expiry + FIFO lots need date/doc/qty/price detail | NXT exists, moves start empty | none |
| WIP 154 by project/order/contract | no project object | none |
| TSCĐ/CCDC/242 opening + remaining life | masters exist, no opening state | none |
| Bank per account (master first) | `opening_balance` create-field only | partial |
| Generic GL + two-book split | neither | none |
| Excel import + row validation + delete-reload | docs→MD only | none |
| SKU totals = 152/153/155/156/157/158 check | no check | none |
| Year-roll + prior-year fix refresh | no close chain | none |
| 341 by contract, consignment flags, FX opening | absent | none |

## 5. Risks if PROD without brick (P0)

Tax (wrong VAT/CIT, NĐ310 fines) → Audit (qualified opinion) → Legal (broken 10y chain) → Ops (stockouts, missed collections, double payments, zero cost basis) → Adoption (no import path vs MISA).

## 6. Roadmap pointer

5 sprints in `ROADMAP.md` (S1 GL+bank → S2 AR/AP → S3 stock → S4 FA/CCDC/WIP → S5 Excel+gate+year-roll). Flag `opening.enabled=false` until S1–S3 + gate green.

---
*BA Lead + Chief Accountant review. Codegraph + git sync verified. Law re-checked 2026-09-04.*
