# Use Cases: Company Module

Personas:
- **A** — Admin / Giám đốc
- **CA** — Chief Accountant / Kế toán trưởng
- **SA** — Staff Accountant / Kế toán viên

---

## UC-01: Initial Company Setup (One-Time, Mandatory)

**Actor:** CA, with A confirmation
**Preconditions:** Company registered with GDT (has MST, ĐKKD); this is FIRST-RUN of system

### Happy Path
1. A accesses system first time; system detects no companies
2. System routes to `/companies/new` setup wizard
3. CA fills legal info: legal_name, MST, headquarters_address, legal_representative
4. CA fills registration: business_reg_number, business_reg_date
5. CA selects company_type: MULTI_LLC
6. System derives: accounting_regime=TT99 (default for LLC)
7. CA fills accounting info: fiscal_year_start (1/1), responsible_accountant_name + license
8. CA fills tax info: tax_agency, controlling_tax_office
9. CA fills BHXH: bhxh_code, bhxh_agency
10. CA enters bank accounts (primary + backup)
11. System validates: MST format, all required fields non-empty, fiscal year valid
12. CA confirms: "I certify this matches our business registration"
13. CA stamps: legal_reviewed_at = now, legal_reviewed_by = CA user
14. System writes Company record; emits `COMPANY_CREATED` audit event
15. System creates CompanyConfig for this company (from system-settings module)
16. System: config_version=1, status=ACTIVE
17. A confirms: "Ready for operations"

### Alternative Path — Household Business (Hộ KD)
1. CA selects company_type=HOUSEHOLD
2. System switches: accounting_regime=TT58_MICRO (simplified)
3. System disables: consolidated BCTC template, auditor requirement check
4. BHXH code optional (Hộ KD not required to register separate BHXH unless has employees)
5. Setup completes in ~15 min vs ~30 min for enterprise

### Alternative Path — Fiscal Year Apr-Start
1. CA selects fiscal_year_start_month=4, day=1
2. System derives: FY2026 runs Apr 2026 – Mar 2027
3. System configures: period numbering Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar
4. System flags: "Current accounting period (Jan 2026) belongs to FY2025"

### Exception Paths
- **EX-01:** MST format invalid → 422 INVALID_MST: "MST không hợp lệ (10 chữ số hoặc XXXXXXXXXX-XXX)"
- **EX-02:** MST already exists in system → 409 MST_TAKEN: "MST này đã được đăng ký"
- **EX-03:** BHXH code missing for LLC → 422: "Mã BHXH là bắt buộc cho công ty TNHH"
- **EX-04:** Concurrent setup by two admins → Optimistic lock conflict on INSERT companies → retry
- **EX-05:** Setup skipped → all write operations rejected with `CompanyNotInitializedError`

---

## UC-02: Update Company Info (Change Notification Simulation)

**Actor:** A or CA
**Preconditions:** Company exists, status=ACTIVE

### Happy Path — Non-Restricted Field
1. A requests company detail: GET /companies/{id}
2. System returns current company info + flags restricted fields: `legal_name`, `mst`, `company_type`, `business_reg_number`
3. A requests: PATCH phone, email, short_name
4. System: validates user has ADMIN role
5. System: checks none of the changed fields are RESTRICTED
6. System: updates company; config_version++
7. System: emits `COMPANY_UPDATED` audit event (before/after)
8. System: invalidates cache

### Alternative Path — Restricted Field (Legal Name Change)
1. A tries to PATCH legal_name
2. System returns: 422 LEGAL_CHANGE_REQUIRES_REREGISTRATION: "Thay đổi tên doanh nghiệp yêu cầu đăng ký bổ sung tại Sở KH&ĐT"
3. System provides: Mẫu số 12 workflow
4. CA files Mẫu 12 with DPI; receives confirmation
5. CA returns with new ĐKKD scan
6. CA submits: PATCH with `legal_name_change_pending=true` + `mẫu_12_reference=...`
7. System: marks company for update; creates change record
8. Upon DPI confirmation (future: API integration with dichvucong.gov.vn):
   - System: updates legal_name
   - System: sets mst_changed_at if MST also changed
   - System: emits `COMPANY_LEGAL_INFO_CHANGED` audit event with before/after

### Exception Paths
- **EX-01:** MST change attempted after any invoice posted → 409 MST_CHANGE_BLOCKED: "Không thể đổi MST sau khi đã phát hành hóa đơn"
- **EX-02:** Company type change without re-registration proof → 422 LEGAL_CHANGE_REQUIRES_REREGISTRATION
- **EX-03:** Legal rep change during locked period → 422: "Cannot change legal rep during FYEAR_CLOSED period"

---

## UC-03: Suspend / Reactivate Company

**Actor:** CHIEF_ACCOUNTANT
**Preconditions:** Company exists; reason documented

### Happy Path — Suspend
1. CA requests: POST /companies/{id}/suspend
2. System: checks CHIEF_ACCOUNTANT role
3. System: checks no open periods (PeriodLock check)
4. System: checks no DRAFT invoices/vouchers
5. System: sets status=SUSPENDED, is_active=FALSE
6. System: emits `COMPANY_SUSPENDED` audit event with reason
7. SA attempts to create invoice for this company → 403 COMPANY_SUSPENDED
8. SA creates invoice for different company (if multi-company) → allowed

### Exception Paths
- **EX-01:** Open periods exist → 409 COMPANY_HAS_OPEN_PERIODS: "Khóa sổ tất cả kỳ trước khi tạm ngừng"
- **EX-02:** DRAFT vouchers exist → 422: "Có 3 chứng từ chưa đăng sổ. Đăng sổ hoặc huỷ trước."

---

## UC-04: Add Bank Account

**Actor:** A or CA
**Preconditions:** Company ACTIVE

### Happy Path
1. A requests: POST /companies/{id}/bank-accounts
2. Body: `{ "bank_name": "VCB", "account_number": "0071234567890", "account_holder": "Công ty TNHH ABC", "branch": "PGD Quận 7", "is_primary": true }`
3. System: validates account_number format (Vietnamese bank: 10-13 digits or alphanumeric per bank)
4. System: adds to bank_accounts list
5. System: emits `BANK_ACCOUNT_ADDED` audit event

### Exception Paths
- **EX-01:** Duplicate account_number → 422: "Số tài khoản đã tồn tại"
- **EX-02:** Setting is_primary=true when primary already exists → system swaps old to false, sets new as primary

---

## UC-05: MST Change (Post-Registration)

**Actor:** A + External: GDT Tax Authority
**Preconditions:** GDT has issued new MST (company merged, reorganized, or corrected)

### Happy Path
1. GDT issues new MST via official letter
2. CA files Mẫu 47 notification with new MST
3. CA submits: POST /companies/{id}/change-mst
   Body: `{ "new_mst": "9876543210", "gdt_notification_ref": "MT-2026-0089", "effective_date": "2026-09-01" }`
4. System: validates new MST format + uniqueness
5. System: sets mst_changed_at = effective_date
6. System: locks all invoices with issue_date >= effective_date for batch re-tagging
7. System: emits `MST_CHANGED` audit event (old_mst, new_mst, effective_date)
8. CA: reprints invoices from effective_date onward with new MST on batch job
9. Historical invoices (before effective_date) retain old MST — legally valid

### Exception Paths
- **EX-01:** New MST already in use → 409 MST_TAKEN
- **EX-02:** No GDT notification reference → 422: "Yêu cầu thông báo cơ quan thuế"
- **EX-03:** Effective date in past without justification → 409: "effective_date must be today or future"

---

## UC-06: Legal Review Stamp (Company Level)

**Actor:** CA
**Preconditions:** Company exists; setup complete; initial review pending

### Happy Path
1. System: flags company for legal review after creation
2. CA navigates: GET /companies/{id}/legal-review
3. System returns: company info + checklist:
   - Legal name matches ĐKKD ☐
   - MST valid and active in GDT database ☐
   - Accounting regime matches company type ☐
   - Responsible accountant license valid ☐
   - BHXH code registered ☐
4. CA reviews; all items checked
5. CA submits: POST /companies/{id}/legal-review
6. System: sets legal_reviewed_at, legal_reviewed_by
7. System: emits `COMPANY_LEGAL_REVIEW_STAMPED` audit event
8. Company considered LEGAL_REVIEWED; invoices can be issued

### Exception Paths
- **EX-01:** BHXH code not validated → 422: "Mã BHXH chưa được xác nhận"
- **EX-02:** MST regex invalid at review time → 422 INVALID_MST
- **EX-03:** Responsible accountant license format invalid → 422: "MSKHMN không hợp lệ"

---

## UC-07: Tenant Access (Multi-Company Future)

**Actor:** SA (multi-company user)
**Preconditions:** User belongs to 2+ companies; multi-company enabled

### Happy Path
1. SA logs in; system sees 2 company memberships
2. System shows company selector: dropdown with company names
3. SA selects "Công ty ABC"
4. System: resolves company_id from selection
5. All subsequent requests scoped to company_id
6. SA sees only ABC's invoices, partners, vouchers

### Exception Paths
- **EX-01:** SA's company is SUSPENDED → 403 COMPANY_SUSPENDED
- **EX-02:** SA has no company membership → 403: "No company access"