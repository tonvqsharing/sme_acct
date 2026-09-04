# BRD — Opening Balance Brick (Số dư ban đầu)

| | |
|---|---|
| Module | Opening Balance — HTK/AR/AP/FA/CCDC/bank/GL opening + Excel import + go-live gate |
| Version | 1.0 — PROD Gap Review |
| Date | 2026-09-04 |
| Authors | BA Lead 20y + Chief Accountant VACPA 20y |
| Depends | Company, COA, FY/Period, Party, UOM, Product/Warehouse/Lot, Bank/Cash, Fixed Assets, CCDC, Audit Log, User/RBAC |
| Status | BRD approved — S1–S5 required before PROD |

## 1. Background & Goal

New company on system holds history elsewhere (old books, Excel, prior vendor). Without lawful opening entry, ledger starts zero → all reports wrong from month one.

Goal: `enter per-object opening → reconcile vs GL → Nợ=Có gate → lock → go-live`. Must satisfy TT99 Điều 22–23 (carryover on conversion/split), VAS 02 (HTK cost), 10y retention root.

```
Objective = complete auditable day-one balances, subledger = GL,
            balanced books, locked before first live voucher.
```

## 2. Regulatory drivers (active only)

```
ACTIVE (2026-09-04)                    OUTDATED — DO NOT USE
─────────────────────────             ────────────────────────────
TT99/2025 (Điều 22,23,30)             TT200/2014 (replaced)
TT58/2026 (SME/micro)                 TT133/2016 + TT132/2018
VAS 02 (HTK cost/NRV)                 LIFO-as-equal (Standard added)
Luật Kế toán 88/2015 Art.11 (10y)     NĐ123/2020 e-invoice (→NĐ254+TT91)
NĐ181/2025 Đ.26 (≥5tr proof)          TT32/2025 (→TT91/2026)
```

## 3. Scope v1.0

In:
1. GL opening per account (Nợ/Có, two-sided, FX amount+rate optional).
2. AR/AP/141/138/338 by Party counterparty (link Party master, proof flag for ≥5tr AP).
3. Stock opening by SKU×warehouse (qty + total value; lot/expiry optional; FIFO/specific need per-receipt date/doc/qty/price rows).
4. WIP 154 header (project ref as text until Project master exists).
5. TSCĐ/CCDC/242 opening (remaining value + months left → feeds depreciation/allocation).
6. Bank per account (account master first).
7. Excel import (template download, row validation, valid-only import, delete-reload).
8. Reconcile: SKU totals = 152/153/155/156/157/158; trial Nợ = Có gate; lock opening after go-live.
9. Year-roll: close year N → opening year N+1; prior-year fix refresh.

Out (v1): two-book split, consignment flags, 341-by-contract, POS opening, TT200→TT99 auto-mapper (manual map table ok).

## 4. Roles

| Action | ADMIN | CHIEF | ACCOUNTANT | AUDITOR |
|---|---|---:|---:|---:|
| Enter/edit opening (pre-lock) | - | ✓ | ✓ | - |
| Lock opening (go-live) | ✓ | ✓ | - | - |
| Reopen locked opening | - | ✓ | - | - |
| Read opening/reports | ✓ | ✓ | ✓ | ✓ |

## 5. Success criteria

| # | Criterion | Measure |
|---|---|---|
| SC-01 | Full opening entry < 1 day for 500-SKU SME (Excel path) | pilot |
| SC-02 | SKU totals = GL 152/156 exactly | UT+integration |
| SC-03 | Unbalanced opening blocked (Nợ≠Có → 422) | UT |
| SC-04 | Post-lock edit blocked (409) without CHIEF reopen | UT |
| SC-05 | FIFO opening replays correct COGS on first out | integration |
| SC-06 | Year-roll carries exact close balances | integration |
| SC-07 | gates green (ruff/black/mypy/pytest) + review Approve | CI |

## 6. Ubiquitous Language

| Term | Meaning |
|---|---|
| Opening (số dư ban đầu) | Day-one balances, pre-first-voucher, locked at go-live |
| Subledger opening | Per-object detail (partner/SKU/lot/account) |
| GL opening | Per-account Nợ/Có totals |
| Reconcile | Subledger totals = GL totals per account |
| Go-live lock | Opening immutable; further change via vouchers only |
| Year-roll | Close N balances → N+1 opening rows |
