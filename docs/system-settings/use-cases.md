# Use Cases: System Settings Module

## UC-01: Config Initialization
**Actor**: Chief Accountant / System Administrator  
**Precondition**: Company entity exists in system; database migration applied  
**Main Success Scenario**:  
1. Chief Accountant logs in with admin role  
2. System presents initial config setup form with legal constants pre-populated from domain defaults  
3. Chief Accountant reviews and confirms: accounting regime, fiscal year start, VAT rates, e-invoice mode  
4. System validates all LAW-type flags are correct per Vietnamese law  
5. Chief Accountant clicks "Initialize System Settings"  
6. System creates CompanyConfig record with config_version=1; emits audit log event  
7. Chief Accountant sees confirmation + legal review stamp required before PROD use  

**Extensions**:  
- E-01: Chief Accountant changes a LAW-type flag → System raises FlagLockedError; requires migration patch  
- E-02: Chief Accountant changes a CONFIG-type flag → System emits audit event before/after; config_version increments  

**Postconditions**: CompanyConfig record exists; config_version=1; audit log has CREATE event; legal_reviewed_at=null (pending review)

---

## UC-02: Period Lock
**Actor**: Chief Accountant / Kế toán trưởng  
**Precondition**: CompanyConfig exists; fiscal year defined  
**Main Success Scenario**:  
1. Chief Accountant selects accounting period (e.g., Q3 2026: 2026-07-01 to 2026-09-30)  
2. System checks PeriodLockService.is_locked(company_id, period_start, period_end)  
3. If not locked: System creates PeriodLock record; emits audit log event  
4. If locked: System raises information that period already locked  
5. Chief Accountant can view locked periods list  

**Extensions**:  
- E-01: Chief Accountant attempts to unlock a locked period → System checks for existing vouchers/invoices in that period; if exists, raises error; if none, unlocks and emits audit event  

**Postconditions**: PeriodLock record exists; audit log has CREATE/DELETE event; period status visible in UI

---

## UC-03: VAT Rate Validation
**Actor**: Any user creating/editing invoice/voucher  
**Precondition**: CompanyConfig exists; VAT rates configured  
**Main Success Scenario**:  
1. User creates invoice with VAT rate field  
2. System validates rate against CompanyConfig.vat_rates frozenset {0, 5, 10}  
3. If valid: Invoice proceeds; subtotal/vat_total/grand_total auto-recalculated  
4. If invalid: System raises InvalidVATRateError; user cannot proceed until corrected  

**Extensions**:  
- E-01: User attempts VAT rate not in allowed set → Error message shows allowed values  

**Postconditions**: VAT rate validated; no invalid rates persisted; totals recalculated correctly

---

## UC-04: E-Invoice Series Management
**Actor**: Chief Accountant / Kế toán trưởng  
**Precondition**: CompanyConfig exists; e-invoice mode configured  
**Main Success Scenario**:  
1. Chief Accountant adds new e-invoice series with prefix (e.g., "AA/2026")  
2. System checks current series count < 15 (max per GDT)  
3. If under limit: System creates EInvoiceSeries record with next_sequence=1, is_active=True  
4. If at limit: System raises SystemSettingsError("Đã đạt giới hạn 15 series")  
5. Chief Accountant can view all series; toggle active/inactive  

**Extensions**:  
- E-01: Chief Accountant modifies series prefix → System raises error (prefix immutable after creation; requires new series)  
- E-02: Chief Accountant deactivates a series → System sets is_active=False; new series can be activated if count < 15  

**Postconditions**: EInvoiceSeries record exists; series count visible in UI; audit log has CREATE event

---

## UC-05: Config Update with Audit
**Actor**: Chief Accountant / Kế toán trưởng  
**Precondition**: CompanyConfig exists; admin authenticated  
**Main Success Scenario**:  
1. Chief Accountant selects config field to change (e.g., VAT method)  
2. System checks flag_type: if LAW → raises FlagLockedError; if CONFIG → proceeds  
3. System emits audit event BEFORE mutation (old value, new value, actor, timestamp)  
4. Chief Accountant confirms change  
5. System updates CompanyConfig; config_version increments; emits audit event AFTER mutation  
6. Chief Accountant sees confirmation + audit trail update  

**Extensions**:  
- E-01: Chief Accountant changes LAW-type flag → System raises FlagLockedError; requires migration patch (documented path)  
- E-02: Concurrent edit detected via config_version mismatch → System raises ConfigVersionConflict; retry required  

**Postconditions**: CompanyConfig updated; config_version incremented; two audit log events (before/after); legal_reviewed_at may be set for LAW changes
