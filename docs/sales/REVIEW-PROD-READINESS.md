# REVIEW — Sales Bricks PROD Readiness (BA Lead 20y + Chief Accountant 20y)

| | |
|---|---|
| Module | Sales — `invoice` + `voucher` + `ledger` (Sổ Nhật ký chung, Bảng CĐPS) |
| Date | 2026-09-03 |
| Reviewers | BA Lead (20y ERP/SME) + Chief Accountant (VACPA 20y) + Legal Research (137 docs, vbpl/mof/gdt/Big4) |
| Gate | `ruff` → `black` → `mypy --ignore-missing-imports` → `pytest -q` = **968 passed** |
| Verdict | **CONDITIONAL PROD — NOT full PROD for external e-invoice sales** |

## 1. TL;DR

```
Invoice + Voucher + Ledger CAN operate in PROD for INTERNAL voucher workflow
(CLOSED company, manual paper/e-invoice outside system).

CAN NOT operate as end-to-end E-INVOICE SALES in PROD without gaps P0-P2 below.
```

| Track | Verdict | Reason |
|---|---|---|
| Internal sales journal (DRAFT→POSTED → Ledger) | **PROD OK** | Gates green: FY open → COA posting → catalog+window+8% category → balanced → checksum → audit |
| VAT declaration input for sales output tax | **PROD OK** | Output via ledger read-model; carry/persist exists |
| E-invoice issuance per NĐ254/2026+TT91 (ký hiệu, ký số, cấp mã, gửi CQT) | **NO** | No mẫu số/ký hiệu, no signing, no GDT submit |
| Revenue recognition per TT99/2025 (multi-element, principal/agent, BĐS) | **GAP** | Single-rate per invoice + flat 511, no unbundling |
| FX sales + discounts/returns (521) | **GAP** | No multi-rate, no sales deductions brick |
| Approval/SOD for sales | **GAP** | Voucher has chief_approved for cash; invoice post has no role gate |

## 2. What is GOOD (keep)

1. **Hexagonal seams respected** — `domain.py` pure, services via ports (`fy`, `coa`, `numbering`, `terms`, `audit`, `regime_of`, `rate_gate`), no cross-brick model joins.
2. **Transaction gate order correct** — `FY open → COA posting (ACTIVE+detail, regime-aware) → balance/invariant`. Ledger never touches voucher models (`LedgerSourcePort`).
3. **VAT law gates implemented**: `ALLOWED_VAT_FRACTIONS` from `TaxRate`, `make_rate_gate()` window by `issue_date` (sunset 31/12/2026 auto), `is_8pct_eligible()` on EVERY line when `rate=0.08` (NĐ174 Art.1). 12 tests cover this.
4. **Numbering SOD** — `system:numbering` UUIDv5 actor, series `HD/`/`PT/` via `DocumentNumberingSeriesService`, seq per-company.
5. **Checksum + audit** — `compute_checksum(prev, actor, reason)` + `audit.append(entity_type=invoice/voucher, action=POST)`.
6. **Tests 968** green 3.11+3.12, unit (fakes) + integration (`create_app(TESTING=True)` real factory).

## 3. Gaps blocking full Sales PROD

### P0 — Must fix before external sales PROD

| # | Gap | Impact | Fix (see specs §5) |
|---|---|---|---|
| P0-01 | **No TT99 revenue recognition** — bundled contracts, principal-vs-agent (net commission), BĐS control transfer not modeled | Misstates revenue per TT99 Ch.II; audit qualification | Introduce `Contract` + `PerformanceObligation` split, deferred revenue 3387, agent path net-only |
| P0-02 | **E-invoice NĐ254/2026 + TT91 missing** — no `ký hiệu mẫu số/ký hiệu hóa đơn`, no 8-digit `số hóa đơn` (1→99,999,999 / year), no signing, no cấp mã / gửi CQT | Cannot legally issue HĐĐT from 01/07/2026 | Add `EInvoiceEnvelope` brick extension + signing + GDT XML (like purchases GDT XML) |
| P0-03 | **Single VAT rate per invoice** — `vat_rate: Decimal` on header | Breaks mixed-rate invoices (5%+10%+8%); forces split invoices unnecessarily | Move VAT to line level `InvoiceItem.vat_rate` + header `vat_breakdown` |
| P0-04 | **No sales deductions (TK 521)** — hàng bán bị trả lại, giảm giá, chiết khấu | P&L overstates 511; TT99 account 521 exists | Add `SalesDeduction` voucher type + 5211/5212/5213 mapping |
| P0-05 | **Invoice post has no RBAC/SOD** — any authenticated can post; no `CHIEF_ACCOUNTANT` gate for material amounts | Violates KSNB & TT99 signing rules (kế toán trưởng not sign on behalf of mgmt) | Add `approval_threshold` gate or at least `AUDITOR` block + `chief_approved` for >X |

### P1 — Should fix for SME PROD completeness

| # | Gap |
|---|---|
| P1-01 | FX sales: `invoice` has no `currency_code/fx_rate/amount_original`; voucher has it. Export sales (0% VAT) in USD not possible via invoice path. |
| P1-02 | Inventory/COGS linkage: sales does not emit 632; no tie to `156/155` stock. |
| P1-03 | Payment collection tracking: `due_date` computed but no `receipt` → `AR aging` → `reconciliation` for 131. |
| P1-04 | Checksum fragility: `compute_checksum` hashes `grand_total` only, not items — item mutation undetected. Hash canonical `items+vat_breakdown`. |
| P1-05 | Ledger pagination/period lock: `general_journal` loads all `get_posted_lines` unbounded; no period-lock read guard (SystemSettings period_lock exists but not wired to sales). |
| P1-06 | Approval workflow docs (`docs/brd/approval-workflows-brd.md`) not implemented — amount thresholds + splitting detection + delegation absent. |

### P2 — Nice to have

- Contract asset handling, multi-currency revaluation hooks, B01/B02/B03 sales note disclosures.

## 4. Laws double-checked (2026-09-03) — outdated REMOVED

```
OUTDATED (DO NOT USE)            REPLACED BY (LAW IN FORCE)
─────────────────────────────    ──────────────────────────────────────────────
TT200/2014/TT-BTC                → TT99/2025/TT-BTC (27/10/2025) FY≥01/01/2026
TT132/2018/TT-BTC (SME)           → TT58/2026/TT-BTC (SME, 2026)
NĐ123/2020 + NĐ70/2025 + TT32/2025 → NĐ254/2026/NĐ-CP (30/06/2026) + TT91/2026/TT-BTC (01/07/2026)
NĐ41/2018 etc.                  → NĐ181/2025 + NĐ144/2026 (sửa) + TT69/2025
Circular 39/2014 e-invoice        → NĐ254/2026 + TT91/2026 (HĐĐT)
```

Verified sources: vbpl.vn, mof.gov.vn, thuvienphapluat.vn, chinhphu.vn (NĐ254 full text 30/06/2026 5 chapters 45 arts, hiệu lực 01/07/2026), ketoananthienung, ketoanleanh.edu.vn, webketoan, Forvis Mazars 2026-07-24 TT99 note, Incorp 2025-12-02, Grant Thornton Dec 2025, Acclime.

Active drivers for Sales:

- **VAT**: Luật GTGT 48/2024/QH15 (0/5/10) + NQ204/2025 + NĐ174/2025 (10→8% 01/07/2025→31/12/2026) + EXCLUDED categories.
- **E-invoice**: NĐ254/2026 Art.10 + Phụ lục → bắt buộc `tên HĐ, ký hiệu mẫu số, ký hiệu HĐ, số HĐ (8 chữ số, 1→99,999,999/năm/cặp ký hiệu), thông tin người bán/mua, thuế suất`.
- **Accounting**: TT99/2025 (enterprise) + TT58/2026 (SME) — flexible CoA but must back by internal regulation; revenue recognition: control transfer, multi-PO unbundling, agent net, BĐS no schedule.
- **Signing**: TT99 — kế toán trưởng NOT sign on behalf of directors.
- **Retention**: Luật Kế toán 2015 Art.11 — 10y.

## 5. Existing code map (codegraph sync 2026-09-03)

```
src/bricks/invoice/domain.py      — Invoice, InvoiceItem, status DRAFT/POSTED, checksum
src/bricks/invoice/services.py    — InvoiceService (fy→coa→catalog→window→8%→numbering→terms)
src/bricks/invoice/storage.py     — invoices table, items as JSON, SQLAlchemyInvoiceRepository
src/bricks/invoice/web_adapter.py — POST/GET /api/v1/invoices, POST /.../post → auto-journal via app.py

src/bricks/voucher/*              — JournalLine (debit XOR credit), Voucher balanced TOLERANCE 0.01
                                    VoucherService + on_posted cash side-effects + bank adjust
src/bricks/ledger/services.py     — general_journal (grouped by entry_date|number), trial_balance
src/bricks/ledger/storage.py      — SQLAlchemyLedgerSource (reads voucher lines only POSTED)

Wiring in src/app.py:
  COA + FY → _FyGate/_CoaGate → VoucherService (+_apply_cash_balances, _SeriesIssueAdapter PT/)
           → InvoiceService (same gates + RATE_GATE + allowed fractions + _TermsAdapter, HD/)
           → auto_journal = AutoJournalService(lines_from_invoice)
  LedgerSource → LedgerService + VatDeclaration input/output
```

## 6. Roadmap to full Sales PROD (execution plan in docs/sales/ROADMAP.md)

1. **Sprint 1 (P0-03 + P0-05)**: line-level VAT + RBAC gate — no law change, isolated.
2. **Sprint 2 (P0-04)**: 521 deductions voucher type.
3. **Sprint 3 (P0-01)**: TT99 multi-PO + deferred revenue (largest domain change).
4. **Sprint 4 (P0-02)**: NĐ254 e-invoice envelope + GDT XML + signing seam (reuse purchases XML pattern).
5. **Sprint 5 (P1 hardening)**: FX, COGS, AR aging, checksum hardening, pagination.

## 7. Recommendation

- **Today**: keep Sales bricks for **internal PROD** (single-rate VND sales, manual e-invoice outside). Add feature flag `sales.e_invoice_enabled=false` to block external claim.
- **Before external PROD**: complete P0-01..05 (est. 4 sprints). Do NOT lift flag until e-invoice GDT round-trip tested against `thuedientu.gdt.gov.vn` sandbox.

---
*Generated by BA Lead + Chief Accountant review. Codegraph + git sync verified. Law re-checked 2026-09-03.*
