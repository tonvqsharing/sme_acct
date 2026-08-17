# Workflows: System Settings Module

## WF-01: System Settings Initialization Workflow
**Trigger**: Chief Accountant first-time setup after company creation  
**Precondition**: Company entity exists; database migration (versions/xxx_system_settings_phase_1.py) applied  
**Step-by-Step**:  
1. Chief Accountant accesses System Settings page via main menu  
2. System displays initialization form with legal constants from domain defaults  
3. Chief Accountant reviews each field (accounting regime, fiscal year, VAT rates, e-invoice mode)  
4. Chief Accountant clicks "Validate Legal Compliance" → System checks all LAW-type flags against Vietnamese law  
5. If validation passes: System enables "Initialize" button  
6. Chief Accountant clicks "Initialize System Settings"  
7. System creates CompanyConfig record; config_version=1; emits AuditLogService.CREATE event  
8. System displays confirmation: "Cấu hình hệ thống đã được khởi tạo"; legal_reviewed_at=null (pending chief accountant review)  
9. Chief Accountant reviews confirmation; clicks "Mark as Reviewed" → System sets legal_reviewed_at=now  
10. Workflow completes; system redirects to main config dashboard  

**Alternative Paths**:  
- A-01: Chief Accountant clicks "Validate Legal Compliance" → System finds LAW-type flag misconfiguration → Error message lists non-compliant fields + legal basis  
- A-02: Chief Accountant attempts to initialize without Company entity → System raises CompanyNotFoundError  

**Postconditions**: CompanyConfig exists; audit log has CREATE event (initialization); legal_reviewed_at set after chief accountant review; config_version=1

---

## WF-02: Period Lock/Unlock Workflow
**Trigger**: Chief Accountant locking/unlocking an accounting period  
**Precondition**: CompanyConfig exists; fiscal year defined (e.g., 2026: Jan 1 - Dec 31)  
**Step-by-Step - Lock**:  
1. Chief Accountant selects period: start_date, end_date (e.g., Q3: 2026-07-01 to 2026-09-30)  
2. System checks PeriodLockService.is_locked(company_id, start_date, end_date)  
3. If already locked: System shows "Ky khóa này đã được khóa" + lists who locked it + audit log link  
3. If not locked: System creates PeriodLock record; configures period_start, period_end, is_locked=True; emits AuditLogService.CREATE event  
4. System displays confirmation: "Ky khóa kì kế toán [start_date] - [end_date] đã được khóa"  
5. System disables voucher/invoice posting for that period at service layer  

**Step-by-Step - Unlock**:  
1. Chief Accountant selects locked period to unlock  
2. System checks for existing vouchers/invoices in that period  
3. If vouchers/invoices exist: System raises error "Không thể mở khóa: còn chứng từ/posting trong kì này"; shows count + link to view them  
4. If no vouchers/invoices: System creates PeriodLock record with is_locked=False; emits AuditLogService.DELETE event  
5. System displays confirmation: "Ky khóa kì kế toán [start_date] - [end_date] đã được mở khóa"  

**Alternative Paths**:  
- A-01: Chief Accountant attempts to lock a period that overlaps with a closed fiscal year → System error + legal basis reference  
- A-02: Chief Accountant attempts to unlock a period with existing vouchers → Error shows details + option to void/post those vouchers first  

**Postconditions**: PeriodLock record reflects correct state; audit log has CREATE/DELETE event; service layer blocks/posting enabled for correct periods

---

## WF-03: Config Update with Audit Workflow
**Trigger**: Chief Accountant/Admin modifying a system configuration flag  
**Precondition**: CompanyConfig exists; admin authenticated with appropriate role  
**Step-by-Step**:  
1. Admin selects config field to modify (e.g., VAT method: DEDUCTION → OUTPUT_ONLY)  
2. System reads current value + flag_type (LAW vs CONFIG)  
3. If flag_type == LAW: System raises FlagLockedError with message "Cờ hệ thống LAW không thể thay đổi mà không có migration patch" + legal basis reference  
4. If flag_type == CONFIG: System proceeds to step 4  
5. System emits AuditLogService event BEFORE mutation: {flag_name, old_value, new_value, actor_id, timestamp, table_name}  
6. System updates CompanyConfig field; config_version increments atomically  
7. System emits AuditLogService event AFTER mutation: {flag_name, new_value, actor_id, timestamp, table_name, config_version}  
8. System displays confirmation: "Cấu hình '{flag_name}' đã được cập nhật"; new config_version displayed  
9. Chief Accountant may set legal_reviewed_at=now if the change has legal implications  

**Alternative Paths**:  
- A-01: Admin changes LAW-type flag → FlagLockedError + detailed message + link to migration documentation  
- A-02: Concurrent edit detected → System raises ConfigVersionConflict; shows current version + requested version; forces re-read + retry  

**Postconditions**: CompanyConfig updated; config_version incremented; two audit log events (before/after); optionally legal_reviewed_at set


---