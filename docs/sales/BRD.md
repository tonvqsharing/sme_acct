# BRD — Sales Module (Invoice / Voucher / Ledger)

| | |
|---|---|
| Module | Sales — SMEs, B2B invoices + sales deductions + e-invoice |
| Version | 1.0 — Sales PROD Gap Review |
| Date | 2026-09-03 |
| Authors | BA Lead 20y + Chief Accountant VACPA 20y + Legal Research |
| Stakeholders | Kế toán viên, Kế toán trưởng, Giám đốc, Auditor, CQT (GDT) |
| Depends | Company, COA (TT99/TT58), FY/Period, Payment Terms & Numbering, System Settings (VAT 8% windows), Bank/Cash, Audit Log, User/RBAC |
| Status | BRD approved — P0 gaps to be closed before external e-invoice PROD |

## 1. Background & Goal

SME phải lập hóa đơn bán hàng, ghi nhận doanh thu, kê khai thuế GTGT đầu ra, và lưu trữ HĐĐT per NĐ254/2026 (01/07/2026).

**Goal**: bán hàng `tạo → (phê duyệt) → phát hành HĐĐT → ghi sổ (debit 131 / credit 511 + 3331) → sổ cái → tờ khai GTGT 01/GTGT`. Must satisfy TT99/2025 revenue principles (control, multi-PO, agent net) while keeping 10-year audit chain.

```
Objective = compliant sales in VND (+FX), correct VAT (0/5/8/10/-1), correct COA,
            e-invoice per NĐ254, auditable, period-locked, SOD-enforced.
```

## 2. Regulatory drivers (active only — outdated struck)

```
ACTIVE (2026-09-03)                           OUTDATED — DO NOT REFERENCE
─────────────────────────────────────────    ────────────────────────────
Luật Kế toán 88/2015/QH13 (10y retention)     TT200/2014 (replaced TT99)
Luật QLT 108/2025/QH15 (01/07/2025)            TT132/2018 (replaced TT58/2026)
Luật GTGT 48/2024/QH15 (0/5/10/-1)             NĐ123/2020, NĐ70/2025, TT32/2025
NQ204/2025 + NĐ174/2025 (8% till 31/12/2026)   (replaced by NĐ254+TT91)
TT99/2025/TT-BTC (enterprise, FY≥2026)        Circular 39/2014 (HĐĐT old)
TT58/2026/TT-BTC (SME)                        NĐ41/2018 (pre-2025)
NĐ254/2026 (30/06) + TT91/2026 (01/07) HĐĐT   ────────────────────────────
NĐ181/2025 + NĐ144/2026 + TT69/2025 (≥5tr)     
```

## 3. Scope

### In scope (v1.0)

1. **Sales invoice lifecycle** DRAFT → POSTED (immutable) with line-level VAT, `ký hiệu + số HĐ`, due date via payment terms.
2. **Revenue recognition per TT99** — control transfer single-PO now; multi-PO + agent net + BĐS in P0-01.
3. **Journal auto-post** — invoice POST → voucher `Nợ 131 / Có 511, Có 3331` (regime-templated codes, 10-digit TT99).
4. **Sales deductions** — hàng bán bị trả lại / giảm giá / chiết khấu → TK 521 → voucher reversing.
5. **Ledger reports** — Sổ Nhật ký chung + Bảng CĐPS (posted-only, chronological).
6. **VAT output** — aggregates for 01/GTGT (input excluded here).
7. **FX sales** — `currency_code + fx_rate + amount_original` on invoice (P1).
8. **E-invoice envelope** — NĐ254: ký hiệu mẫu số/ký hiệu HĐ/số HĐ (8 chữ số), XML signing seam, gửi CQT.

### Out of scope (v1)

- Inventory issuance / COGS 632 (handled by stock brick).
- Collection / AR aging / dunning.
- Marketplace / POS cash sales (máy tính tiền — separate lane).
- Refund workflow beyond voucher reversal.

## 4. Roles & Permissions (Flask `@login_required + current_user.role`)

| Action | ADMIN | CHIEF_ACCOUNTANT | ACCOUNTANT | AUDITOR |
|---|---:|---:|---:|---:|
| Create draft invoice | - | - | ✓ | - |
| Post invoice (< threshold) | ✓ | ✓ | ✓* | - |
| Post invoice (≥ threshold / 8% line) | ✓ | ✓ | - | - |
| Issue e-invoice (sign/send) | ✓ | ✓ | - | - |
| Create deduction 521 | - | ✓ | ✓ | - |
| Read ledger / invoice | ✓ | ✓ | ✓ | ✓ |
| AUDITOR post | - | - | - | **BLOCKED** |

`* ACCOUNTANT posts only if amount < approval threshold AND no 8%-excluded category. Configurable via SystemSettings.*

## 5. Success criteria

| # | Criterion | Measure |
|---|---|---|
| SC-01 | Invoice create <30s, VAT `round(line*rate,0)` VND correct | UT + integration |
| SC-02 | Mixed-rate invoice accepted (e.g., 5% + 10% + 8%) | UT `test_mixed_rates` |
| SC-03 | 8% excluded categories blocked per NĐ174 | UT 9 cats |
| SC-04 | Expired 8% after 31/12/2026 blocked | window gate UT |
| SC-05 | E-invoice XML valid for `thuedientu.gdt.gov.vn` (sandbox) | integration |
| SC-06 | Ledger posted-only, chronological, trial_balance `debit==credit` | ledger UT |
| SC-07 | 10-year audit chain (checksum + audit_log) | audit UT |
| SC-08 | `mypy --ignore-missing-imports` + `ruff` + `black` + `pytest 968+` | CI green 3.11/3.12 |

## 6. Definitions (Ubiquitous Language)

| Term | Meaning |
|---|---|
| Invoice | Chứng từ bán hàng gốc; header + lines; DRAFT→POSTED |
| Performance Obligation (PO) | Nghĩa vụ thực hiện riêng biệt per TT99 — unbundle basis |
| Principal vs Agent | Chủ giao dịch (ghi gross 511) vs môi giới (ghi net commission) |
| Ký hiệu mẫu số | Tax form pattern per NĐ254 Phụ lục (e.g., `1C26TAA`) |
| Ký hiệu HĐ | Series code per NĐ254 (e.g., `HD/`) |
| Deductible 521 | TK 521 — các khoản giảm trừ doanh thu |
| Posted | Immutable; feeds Ledger & VAT output |

## 7. Open questions (resolved for v1)

| Q | Answer |
|---|---|
| VAT stored where? | Line-level `InvoiceItem.vat_rate` + header `vat_breakdown` map |
| E-invoice when? | P0-02 sprint 4 — flag-off until GDT sandbox pass |
| Approval? | Threshold + chief_approved reused from voucher/cash pattern |
| FX? | P1 — mirror voucher `currency_code/fx_rate/amount_original` |

## 8. References

- NĐ254/2026 30/06/2026 (Congbao 402, hiệu lực 01/07/2026) — 5 chapters 45 arts.
- TT91/2026/TT-BTC — hướng dẫn NĐ254 + Luật QLT 108/2025.
- TT99/2025 27/10/2025 — Forvis Mazars 2026-07-24 note + Incorp/Acclime summaries.
- TT58/2026 — SME regime.
- Rate windows law: NQ204+ NĐ174 sunset 31/12/2026.
