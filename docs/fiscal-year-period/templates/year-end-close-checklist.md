# Year-End Close Checklist (Khóa sổ cuối năm)

Kỳ kế toán: **{fiscal_year}** · Công ty: **{company_name}** · Mã số thuế: **{tax_id}**
Người thực hiện: **{name}** · Ngày: **{date}**

## 1. Preconditions (before running close)
- [ ] All 12 periods LOCKED (no OPEN periods)
- [ ] No DRAFT vouchers/invoices in year range
- [ ] No unposted revaluation runs
- [ ] No pending period-close approvals
- [ ] Bank reconciliation complete for all accounts
- [ ] Inventory count adjustments posted

## 2. Month-end checks (per period 1..12)
- [ ] FX revaluation run + posted (if foreign currency)
- [ ] Accruals/prepayments adjusted
- [ ] Depreciation/amortization posted
- [ ] Salary + BHXH/BHYT/BHTN entries posted
- [ ] VAT month entries reconciled

## 3. Kết chuyển (year-end closing entries)
- [ ] Doanh thu → TK 911 (511, 515, 711 ... )
- [ ] Chi phí → TK 911 (632, 635, 641, 642, 811, 821 ... )
- [ ] Kết quả → TK 421 (Lợi nhuận sau thuế chưa phân phối)
- [ ] Verify: TK 911 balance = 0 after appropriation
- [ ] Verify: entries balanced (debit = credit)

## 4. Opening balances (Số đầu năm)
- [ ] Per-account closing balances = new FY opening balances
- [ ] Opening balance entry posted to period 1 of new fiscal year
- [ ] TK 421 carry-forward matches prior year retained earnings

## 5. Post-close
- [ ] New fiscal year created with 12 OPEN periods
- [ ] Old fiscal year status = YEAR_CLOSED
- [ ] BCTC năm generated and archived
- [ ] Lock-event chain checksum verified
- [ ] Tax-declaration cross-check (external)

## Sign-off
| Checked by | Role | Date | Signature |
|---|---|---|---|
| | | | |
