# Use Cases: System Settings / Global Flags Module

Personas:
- **A** — Admin / Giám đốc (highest system role)
- **CA** — Chief Accountant / Kế toán trưởng
- **SA** — Staff Accountant / Kế toán viên
- **AU** — Auditor (external, read-only export access)

---

## UC-01: Company Setup (One-Time)

**Actor:** CA (Chief Accountant), with A confirming
**Preconditions:** Company registered with GDT; MST valid; regime declared to tax authority

### Happy Path
1. CA fills company legal info: name, MST, address, legal rep, company type
2. CA selects accounting regime: `TT200` (default for most enterprises)
3. CA selects chart of accounts: `COA_200`
4. CA selects fiscal year start: `Jan 1` (calendar) or `Apr 1`
5. CA selects VAT regime: `KHẤU TRỪ` or `ĐẦU RA` (pre-configured per tax registration)
6. CA selects VAT settlement cycle: `MONTHLY` (default) or `QUARTERLY`
7. CA reviews all defaults (decimal_places=2, data_retention=10y, cost_center_required=False)
8. CA stamps "Legally reviewed" (signature + date) — sets `legal_reviewed_at`, `legal_reviewed_by`
9. System records `CONFIG_CREATED` audit event with all before/after
10. System returns `CompanyConfig` with `config_version=1`
11. CA conducts 3-entry smoke test to confirm validation works (invalid MST rejected, invalid account code rejected)
12. On success, A authorizes PROD use

### Alternative Path — Fiscal Year Already Started
1. CA sets fiscal year to Apr 1 (FISCAL_APR) mid-Jan (company migrating to Apr FY)
2. System flags: "Changing fiscal year requires BCTC restatement for prior period"
3. CA confirms: system generates closing entries + opening balance migration
4. System records `FISCAL_YEAR_CHANGED` audit event

### Alternative Path — Multi-Regime Company (SME)
1. CA selects `TT58_MICRO` (micro-enterprise regime) for revenue ≤ VND 3B, ≤10 employees
2. System overrides default BCTC disclosure depth to TT58 format
3. System applies simplified VAT rate table (0%, 5%, 10% as applicable)

### Exception Paths
- **EX-01:** MST format invalid at setup → System rejects with message: "MST không hợp lệ (10 chữ số hoặc XXXXXXXXXX-XXX)"
- **EX-02:** CA tries to set both `TT200` AND `TT99` (incompatible) → System raises `InvalidRegimeError` (mutually exclusive enum)
- **EX-03:** Company has foreign-currency transactions but `default_currency=VND` only → System warns: "Multi-currency not enabled; foreign-currency entries will not auto-convert"
- **EX-04:** Concurrent setup by two admins → Optimistic lock conflict; loser's request returns 409; retry with latest version
- **EX-05:** Setup skipped (config_version=0) → System refuses to process any transactions with `CompanyConfigNotInitialized` error

---

## UC-02: Update Config Flag (CONFIG Type)

**Actor:** A (Admin)
**Preconditions:** CompanyConfig exists, config_version known

### Happy Path
1. A requests current config: `GET /config/flags`
2. System returns current values + flag types (LAW vs CONFIG)
3. A selects flag `vat_settlement_cycle` (CONFIG type, requires_2nd_approval=True)
4. A submits PATCH with new value: `quarterly`, X-Config-Version header set to current
5. System checks: flag is CONFIG type ✓, actor has ADMIN role ✓
6. System checks requires_2nd_approval: True → System requests CA confirmation
7. CA receives approval request; confirms
8. System records `CONFIG_CHANGED` before/after in config_changes table
9. System increments config_version (optimistic lock)
10. System invalidates config cache; propagates to all app instances
11. New value effective in <1 second

### Alternative Path — Flag Does NOT Require 2nd Approval
1. Steps 1-4 same; flag is `cost_center_required` (requires_2nd_approval=False)
2. A confirms change; no secondary approval needed
3. Audit log records A as sole approver; event flagged in quarterly review report

### Exception Paths
- **EX-01:** A tries to update LAW-flagged value (e.g., `tax_id_pattern`) → 403 FLAG_LOCKED: "Cannot modify LAW-flag: tax_id_pattern. Requires migration patch."
- **EX-02:** X-Config-Version header missing → 409 with current version in response
- **EX-03:** X-Config-Version header matches but value changed by CA 2 minutes prior → 409 CONFIG_VERSION_CONFLICT; A must re-fetch and confirm
- **EX-04:** CA rejects approval request → Change aborted; 409 returned to A
- **EX-05:** Flag_name not found in config schema → 422 INVALID_FLAG_NAME
- **EX-06:** Value passes type check but fails business rule (e.g., `decimal_places=1`) → 422 INVALID_FLAG_VALUE

---

## UC-03: Close Accounting Period

**Actor:** CA
**Preconditions:** Period is open; all month-end close tasks completed; GL trial balance zeroes out

### Happy Path
1. CA navigates to period status screen: `GET /config/period/status?from=2026-01&to=2026-03`
2. System shows: Jan=LOCKED, Feb=LOCKED, Mar=OPEN
3. CA selects Mar 2026 → POST /config/period/lock with reason "Kết thúc quý 1/2026"
4. System checks: CA has ACCOUNTANT role ✓; period is OPEN ✓
5. System checks: trial balance zero ✓; all March entries posted ✓
6. System creates PeriodLock entry with lock_type=PERIOD, locked_by=CA_user_id
7. System emits `PERIOD_LOCKED` audit event
8. SA attempts to create voucher dated 2026-03-25 → 403 PERIOD_LOCKED
9. SA creates voucher dated 2026-04-01 (next open period) → SUCCESS

### Alternative Path — Close Entire Fiscal Year
1. CA selects FYEAR_CLOSED instead of PERIOD_LOCKED
2. Requires CHIEF_ACCOUNTANT role
3. Additional checks: annual tax declaration submitted; BCTC audited; audit adjustments posted
4. System creates FYEAR_CLOSED lock (highest privilege; immutable without data migration)

### Exception Paths
- **EX-01:** SA tries to backdate invoice to 2026-03-15 after period locked → 403 PERIOD_LOCKED with message showing locked period
- **EX-02:** Period has unposted entries → System returns 409: "Cannot lock: 3 JEs remain DRAFT in March 2026"
- **EX-03:** CA request arrives during parallel lock by another CA → Optimistic lock; second CA gets 409; re-check status
- **EX-04:** SA has admin privilege and tries to force POST → RBAC check at service layer rejects; AUDIT_BREACH_ATTEMPT logged
- **EX-05:** Future period lock attempted → 422 INVALID_PERIOD: "Cannot lock future period"

---

## UC-04: Issue E-Invoice

**Actor:** SA, with approval from CA
**Preconditions:** EInvoiceMode configured; CA list populated if CA_SIGNED mode; invoice series declared to GDT

### Happy Path — Software Cert Mode
1. SA fills invoice form (serial: "AA", invoice_number: auto from series)
2. System reads next_seq from e_invoice_series where prefix="AA/2026"
3. System assigns number, increments sequence atomically
4. CA approves invoice
5. System signs with embedded software certificate
6. System generates XML per GDT schema
7. System emits `INVOICE_ISSUED` audit event with serial+number+timestamp
8. SA prints / sends to customer

### Alternative Path — CA-Signed Mode
1. Steps 1-3 same
2. Before signing, System checks EInvoiceMode=CA_SIGNED
3. System validates signing cert is in ca_list
4. System checks cert expiry date (must not expire within 30 days of invoice validity)
5. System calls signing API (PKI bridge)
6. System attaches signature block to invoice XML

### Exception Paths
- **EX-01:** No series with prefix match → 404: "No active e-invoice series for prefix 'XX/2026'"
- **EX-02:** CA list empty in CA_SIGNED mode → 422: "CA list empty; cannot sign. Update CA list or switch to SOFTWARE_CERT mode."
- **EX-03:** Signing cert not in ca_list → 422: "Certificate DN 'XYZ' not in approved GDT CA list"
- **EX-04:** Series sequence wrap-on (INT overflow) → System raises `InvoiceSeriesExhaustedError`; CA must add new series
- **EX-05:** Invoice period is LOCKED → 403 PERIOD_LOCKED (tested before sequence allocation)

---

## UC-05: Legal Review Stamp

**Actor:** CA
**Preconditions:** Config changes pending; annual review cycle; or post-setup verification

### Happy Path
1. System produces config review summary: list of all flags, current values, who changed them last, when
2. CA reviews for compliance
3. CA stamps with digital signature: "Đã kiểm tra pháp lý / Tôi xác nhận hệ thống đáp ứng quy định kế toán hiện hành"
4. System sets `legal_reviewed_at`, `legal_reviewed_by = CA_user_id`
5. System emits `LEGAL_REVIEW_STAMPED` audit event with summary snapshot stored as JSONB
6. System marks all flag changes since last review as "sanctioned"

### Alternative Path — Post-Setup Initial Review
1. Occurs immediately after company setup (v1 config_version)
2. CA reviews initial values
3. Same stamping process

### Exception Paths
- **EX-01:** Another CA stamps concurrently → Optimistic lock; second CA must re-review (summary may have changed)
- **EX-02:** Stamp attempt within 30 days of last stamp → System warns: "Legal review already stamped 15 days ago; allow for material change?"
- **EX-03:** System flags have LAW-incompatible values (e.g., retention_years=5) → System blocks stamp with error list of violations

---

## UC-06: Auditor Export

**Actor:** AU (auditor), granted read-only access by A
**Preconditions:** Auditor access token provisioned; company audit log exists

### Happy Path
1. AU logs in with auditor credentials (MFA required)
2. A grants AU access to specific company scope via RBAC
3. AU requests: `POST /config/audit-log/export` with date range
4. System collects: full audit_log rows + config_changes rows in date range
5. System generates ZIP with: audit_log.csv, config_changes.json, company_config.json
6. System emits `AUDITOR_EXPORT` event
7. AU downloads; passes to audit evidence management system

### Alternative Path — Ongoing Monitoring
1. AU sets up monthly scheduled export (future: webhook or email)
2. System delivers export at month end automatically

### Exception Paths
- **EX-01:** AU tries to modify config → 403 ROLE_NOT_AUTHORIZED
- **EX-02:** AU requests export for date range not yet migrated → System returns partial data + warning
- **EX-03:** Audit log storage offloaded to cold archive → System retrieves from cold; 5-10 second delay acceptable

---

## UC-07: Add E-Invoice Series

**Actor:** A
**Preconditions:** Company already has <15 active series; series declared to GDT

### Happy Path
1. A requests: `POST /invoice-series` with prefix="BB/2026", ca_signer="VNPT-2026" (optional)
2. System checks: active count < 15 ✓
3. System creates series with active=True, next_sequence=1
4. System emits `INVOICE_SERIES_ADDED` audit event

### Alternative Path — Adding Replacement Series
1. A deactivates old series: `PATCH /invoice-series/AA/2026` with active=false
2. A adds new series BB/2026
3. System preserves AA/2026 sequence history (no reset)

### Exception Paths
- **EX-01:** 15 series already active → 422 MAX_SERIES_EXCEEDED
- **EX-02:** Prefix already exists → 422 DUPLICATE_SERIES
- **EX-03:** Prefix format invalid (e.g., "12345") → 422 INVALID_FLAG_VALUE

---

## UC-08: Detect Flag Violation (System Generated)

**Actor:** System (automated)
**Preconditions:** VAT rate table has `{0,5,10}`; SA tries to enter invoice

### Happy Path (Violation Detected)
1. SA enters invoice line with vat_rate=7 (custom, not in allowed rates)
2. InvoiceService calls SystemSettingsService.validate_vat_rate(company_id, 7)
3. SystemFlags locates `vat_rates` LAW flag → `{0,5,10}`
4. 7 ∉ {0,5,10} → System raises `InvalidVATRateError`
5. UI shows: "Thuế suất 7% không được phép. Chỉ cho phép: 0%, 5%, 10%, NT."
6. System emits FLAG_VIOLATION audit event with flag_name, attempted_value, actor

### Alternative Path — Flag Remediation (after policy change)
1. GDT issues new decree adding 8% VAT rate
2. Admin (C-level approval) applies patch: updates system constant `vat_rates` to `{0,5,8,10}`
3. System emits LEGAL_CONSTANT_UPDATE audit event with new decree citation
4. Invoices with 8% VAT now accepted

---

## UC-09: Quarterly Access Review

**Actor:** A + CA
**Preconditions:** Quarterly cycle; UAR process in place (Big4 requirement)

### Happy Path
1. System produces `USER_ACCESS_REVIEW` report: all users with roles, what they can change, last login
2. A reviews report with CA
3. A deactivates users no longer with company
4. CA verifies role assignments don't violate SoD (no one is both CREATOR + APPROVER + POSTER)
5. A accesses: `GET /access/review?quarter=Q2-2026`
6. Both sign off; system records sign-off as audit event

### Exception Paths
- **EX-01:** SoD conflict detected → System blocks review sign-off until conflict resolved; flags in WARN state
- **EX-02:** User has MFA disabled → System flags as HIGH PRIORITY; blocks sign-off for that user until MFA enabled