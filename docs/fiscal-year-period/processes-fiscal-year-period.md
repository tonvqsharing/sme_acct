# Fiscal Years & Accounting Periods Module — Processes

## P-1 Monthly period close (khóa sổ tháng)

**Trigger**: end of month / monthly BCTC deadline.
**Owner**: Kế toán tổng hợp + Kế toán trưởng.

1. Kế toán tổng hợp verifies: all vouchers posted, invoices issued, no open
   drafts (system lists exceptions).
2. Runs month-end checks: FX revaluation (if applicable), accruals, inventory
   counts, bank reconciliation (Tryton "Closing a period" checklist parity).
3. Requests close via POST `/api/periods/<id>/close` {reason}.
4. Kế toán trưởng approves (SOD) → period LOCKED.
5. System emits lock event + audit record.
6. Post-close: only current period accepts entries; locked-period queries
   read-only.

**Exception**: open items → force + approver re-confirm (UC-04 A2).

## P-2 Year-end close (khóa sổ năm)

**Trigger**: 31/12 (or FY end date).
**Owner**: Kế toán trưởng.

1. All 12 periods locked (P-1 × 12).
2. Preconditions verified: no unposted, no open periods, no pending approvals.
3. Kết chuyển: doanh thu → 911, chi phí → 911, kết quả → 421
   (TT99 chart; Odoo/Tryton P&L appropriation parity).
4. Opening balances per account = closing balances (Số đầu năm).
5. New fiscal year created; opening balance entry posted to period 1.
6. Old FY → YEAR_CLOSED. Reports generated (BCTC năm).
7. Retained-earnings update (Forvis Mazars "update Retained Earnings" parity).

**Exception**: period not locked → 409 with list (UC-07 E1).

## P-3 Fiscal year change (đổi kỳ kế toán)

**Trigger**: business decision (e.g. group reporting alignment, investor demand).
**Owner**: Giám đốc (decision) + Kế toán trưởng (execution).

1. Decision + legal check (Luật 88/2015 Đ12: quarter-aligned start).
2. Notify cơ quan thuế (template in templates/; system tracks
   "đã thông báo" evidence).
3. Close current books.
4. Transition BCTC snapshot (TT133 Đ.73).
5. New FY + periods; opening balances → "Số đầu năm".
6. Consistency locked for ≥ 1 fiscal year (VAS 01).

## P-4 Audit / external examination

**Trigger**: tax audit, statutory audit.
**Owner**: AUDITOR role (read-only) + Kế toán trưởng.

1. Auditors view period history: lock events, checksums, reasons, approvals.
2. Adjustments REQUIRED → reopen workflow (UC-06) with mandatory reason +
   reference; entries posted; period re-locked.
3. Export: full lock-event chain + checksum verification (audit-log parity).

## P-5 Liquidation / dissolution

**Trigger**: company dissolution.
**Owner**: Kế toán trưởng.

1. Final period created (from FY end → dissolution date; <90 days merged).
2. All entries posted; books closed.
3. Final BCTC snapshot archived (audit retention).
4. Certificate of destruction (audit-log module parity) where applicable.

## P-6 System upgrade / migration (FISCAL_15 cleanup)

**Trigger**: deploying this module over legacy data.
**Owner**: admin + Kế toán trưởng.

1. Detect legacy `FISCAL_15` / non-quarter-aligned configs → flag per company.
2. Block posting until fiscal year redefined (R-15).
3. Admin redefines per law; transition handled like P-3.
4. Old data retained in history; labels show "Legacy".
