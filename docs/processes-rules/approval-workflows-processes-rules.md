# Processes and Rules: Approval Workflows / Thresholds

## Processes

### P-01: Invoice Creation and Initial Threshold Check

**Purpose:** Every invoice enters the system with automatic threshold evaluation.

**Steps:**
1. User creates invoice via UI → invoice initialized with `status=DRAFT`
2. `Invoice.add_item()` called for each line item → recalculates `subtotal`, `vat_total`, `grand_total`
3. **Threshold Service** runs automatically post-creation:
   - Retrieve company's threshold matrix from `approval_thresholds` table
   - Evaluate: `invoice_amount` against T1, T2, T3, T4, T5 bands
   - Determine: `band_id`, `approver_role`, `auto_approve_condition`
   - Check: `po_matched` (if invoice has PO reference, validate against existing PO)
   - Check: `splitting_detection` (if vendor has recent invoices within 24h)
4. **Routing decision:**
   - `amount ≤ T1 AND po_matched` → auto-set `status=APPROVED`, audit `auto_approve`
   - `amount ≤ T1 AND NOT po_matched` → route to manager (T2 path)
   - `T1 < amount ≤ T2` → route to MANAGER
   - `T2 < amount ≤ T3` → route to CHIEF_ACCOUNTANT
   - `T3 < amount ≤ T4` → route to DIRECTOR
   - `amount > T4` → route to ADMIN/BOARD
5. Notification sent to assigned approver via RBAC-enforced endpoint
6. Audit log entry created: `action=threshold_check`, `band_id`, `approver_role`, `amount`, `timestamp`

**Triggers:** `POST /invoices`, `Invoice.__init__()`, `Invoice.add_item()`

---

### P-02: Approval Execution

**Purpose:** Assigned approver reviews and acts on pending invoice approvals.

**Steps:**
1. Approver logs in → sees pending approvals badge count
2. Approver clicks invoice → full invoice context displayed (vendor, items, totals, PO, etc.)
3. Approver evaluates: amount validity, vendor compliance, tax correctness, business necessity
4. Approver clicks "Approve" or "Reject"
5. System validates RBAC: `@casbin_required('ROLE')` decorator checks:
   - Approver has required role (MANAGER/CHIEF_ACCOUNTANT/DIRECTOR/ADMIN)
   - If delegation active → delegate acts on behalf, audit records delegation
   - Self-approval blocked: `creator_id != current_user_id` → ValidationError
6. Status updated:
   - `DRAFT → APPROVED` (on approve)
   - `DRAFT → REJECTED` (on reject)
7. Audit log entry created:
   - `action=approve` or `action=reject`
   - `actor=approver_role`, `actor_id=approver_user_id`
   - `amount`, `threshold_band`, `delegation_id` (if applicable)
8. If all invoices in approval chain approved → invoice proceeds to payment run
9. If any invoice rejected → approval chain stops, invoice returns to creator with reason

**Triggers:** Approver UI action, `@casbin_required` decorator enforcement

---

### P-03: Threshold Configuration Update (2nd Approval Pattern)

**Purpose:** Update threshold matrix per Vietnamese accounting Circular 99/2025 requirements.

**Steps:**
1. **Admin proposes** new thresholds via System Settings → Thresholds page
2. System validates:
   - Bands in ascending order: `T1.max_amount < T2.max_amount < T3.max_amount < T4.max_amount`
   - Within reasonable bounds: min $1, max $1,000,000 (configurable)
   - At least 5 bands (T1-T5) maintained
3. Since CONFIG-type flag (per existing SystemSettings pattern):
   - `config_version` incremented: `from N → N+1`
   - Before values captured in audit log
   - Proposal status: `pending_2nd_approval`
   - Notification sent to CHIEF_ACCOUNTANT
4. **Chief Accountant reviews** proposed changes:
   - Reviews for business alignment, compliance, reasonableness
   - Clicks "Approve 2nd" or "Reject"
5. **If 2nd approval received:**
   - `config_version` incremented again: `N+1 → N+2`
   - New thresholds saved to `approval_thresholds` table
   - `cache_invalidation()`: all pending invoices (status=DRAFT) re-evaluated against new thresholds
   - Old thresholds archived in audit log (config_version history)
   - Notification: "Thresholds updated effective [date]"
6. **If 2nd approval not received within 7 days:**
   - Proposal expires
   - `config_version` reverts
   - Admin must resubmit

**Related Policies:** 
- Existing SystemSettings: CONFIG-type flags require 2nd approval + audit log (P-05 pattern)
- LAW-type flags: require migration patch (see P-08)

**Triggers:** `PUT /system-settings/thresholds`, Admin UI action

---

### P-04: Splitting Detection and Prevention

**Purpose:** Detect and prevent invoice splitting to bypass approval thresholds.

**Steps:**
1. **System algorithm** runs post-invoice-creation (every 5 min batch, + real-time on each new invoice):
   - Query: `SELECT * FROM invoices WHERE vendor_tax_id = NEW.vendor_tax_id AND created_at >= NOW() - INTERVAL '24 hours'`
   - If ≥2 invoices found:
     - Calculate: `total_amount = SUM(amount)`, `individual_amounts = [list]`
     - Check: `all(individual < next_threshold_band_max)` → e.g., all < $5K for T2
     - Check: `total_amount > next_threshold_band_max` → e.g., total > $5K
     - If both conditions met → **SPLITTING DETECTED**
2. **Create splitting event record:**
   - `splitting_events` table: detection_id, vendor_tax_id, triggering_invoice_ids, individual_amounts, total_amount, threshold_bypassed, status='pending_review'
3. **Route both invoices** to chief accountant:
   - Bypass normal threshold check for both invoices
   - Approval Router: `status` remains DRAFT, route to CHIEF_ACCOUNTANT regardless of individual amounts
4. **Chief accountant reviews:**
   - Sees splitting alert with both invoices side-by-side
   - Evaluates: legitimate business reason vs. threshold bypass
   - If legitimate: approves with "splitting_override" justification, audit records override
   - If bypass: rejects both invoices, pattern noted for vendor review
5. **Post-approval:**
   - Both invoices proceed to payment (if approved) or return to creator (if rejected)
   - Vendor splitting pattern incremented in system memory
   - If vendor has ≥3 splitting events in 30 days → auto-alert admin, recommend payment term review

**Triggers:** `POST /invoices` (real-time check), batch job every 5 min

**Related Rules:** R-005 (splitting detection), R-009 (splitting triggers chief accountant review regardless of amount)

---

### P-05: Delegation of Authority Management

**Purpose:** Temporary transfer of approval authority when approver unavailable.

**Steps:**
1. **Delegator** (chief accountant) sets up delegation before absence:
   - Access: System → Settings → Delegation Management
   - Input: delegate user ID, effective_from, effective_to (≤30 days), scope, reason
   - System validates:
     - delegator has CHIEF_ACCOUNTANT role
     - delegate has CHIEF_ACCOUNTANT or ADMIN role
     - `effective_to - effective_from ≤ 30 days` (reject if longer)
     - No existing active delegation for delegator (or allow override with justification)
   - Record created in `approval_delegations` table
   - Notification: delegate receives "You have been designated as delegate for [delegator]"
2. **During delegation period:**
   - Delegator's pending approvals flagged in system
   - Delegate logs in → sees: "5 pending approvals (on behalf of Chief Accountant)"
   - Delegate acts on invoices via normal UI
   - `@casbin_required('CHIEF_ACCOUNTANT')` but delegation flag present in DB
   - System: "approve on behalf of delegator, audit records delegation"
   - Audit log: `action=approve`, `approver=DELEGATE (on behalf of CHIEF_ACCOUNTANT)`, `delegation_id` referenced
3. **Delegation expiry (automatic):**
   - On `effective_to` date: system auto-expires delegation
   - Notifications: "Chief accountant approvals resumed, delegation expired"
   - Any remaining pending approvals: revert to chief accountant
   - Notifications: "Approval returned to original approver after delegation expiry"
4. **Early cancellation:**
   - Delegator can cancel early via UI
   - System: "delegation cancelled early, original approver resumes"
   - Audit log: `action=delegation_cancelled`, `delegation_id`, `cancelled_by`, `cancelled_at`

**Related Rules:** R-006 (delegation expiry ≤ 30 days), R-010 (remember last re-basing date)

**Triggers:** `POST /approval/delegations` (create), system cron (expire delegations), UI action (cancel)

---

### P-06: Annual Threshold Re-Basiling

**Purpose:** Align thresholds with actual invoice distribution after 12 months of operation.

**Steps:**
1. **Admin reviews** 12 months of invoice distribution data (export from analytics/Reports)
2. **Analyze:**
   - Invoice count and dollar amount by current threshold band
   - Identify: bands handling disproportionate volume or too few invoices
   - Check: splitting event patterns, delegation frequency
   - Document: business changes in past year (new products, new vendors, volume growth/reduction)
3. **Admin proposes** new thresholds via proposal template (T-005)
4. **2nd approval** (chief accountant) received within 7 days (per P-03 pattern)
5. **New thresholds active:**
   - `config_version` incremented
   - Cache invalidation: all pending DRAFT invoices re-evaluated
   - Old thresholds archived in audit log with re-basing event marker
6. **Notification to stakeholders:**
   - Email to admin, chief accountant, AP team
   - "Thresholds re-based effective [date], new matrix active"
   - Training if significant changes (e.g., T2 threshold increased/reduced >20%)
7. **Document in Re-Basing Report** (T-006) and file for audit compliance

**Timing:** Typically at fiscal year start or company anniversary date  
**Frequency:** Annual (can be triggered earlier if business model changes >20% in invoice patterns)  
**Related Processes:** P-03 (threshold config update), P-05 (delegation - may change with new thresholds)

**Triggers:** Admin-initiated, typically annual; also triggered by P-02 findings or business change

---

### P-07: Audit Compliance Review

**Purpose:** Verify approval workflow compliance with internal policy and Vietnamese regulations.

**Steps:**
1. **Auditor** accesses audit logs module with filter options:
   - `entity_type=invoice`
   - `action IN ('auto_approve', 'approve', 'reject', 'splitting_override', 'threshold_config_update', 're_basing')`
   - Date range (quarterly, annually)
   - Company filter (if multi-company)
2. **Query** generates report data:
   - Total invoices by action type
   - Approval cycle times (submitted_at to approved_at)
   - Threshold band distribution
   - Splitting event counts and resolutions
   - Delegation usage and expiry
   - Self-approval block attempts (should be 0)
   - LAW-type config change attempts blocked (should be 0)
3. **Auditor reviews** for:
   - All threshold checks performed (no bypasses)
   - Approver roles correct per band (MANAGER for T2, CA for T3, etc.)
   - No self-approval successes (system block effective)
   - Splitting events properly handled (override or reject)
   - Config changes followed 2nd approval pattern (CONFIG-type)
   - LAW-type changes require migration (zero incidents in period)
   - Delegations within 30-day max (zero >30-day delegations)
4. **Generate compliance report** (T-008 template)
5. **Distribute** to: admin, chief accountant, board (if material findings)
6. **Track action items** from recommendations, close in next review cycle

**Frequency:** Quarterly (recommended) or annually  
**Related Processes:** P-03, P-04, P-05, P-06  
**Triggers:** Scheduled (quarterly/annual) or ad-hoc (if compliance concern raised)

---

### P-08: LAW-Type Threshold Change Migration

**Purpose:** Handle threshold changes for LAW-type flags (if any threshold parameters declared as LAW-type).

**Background:** Per existing SystemSettings pattern (AGENTS.md: "LAW-type flags immutable without migration; CONFIG-type admin-changeable with audit log + 2nd approval").

**Steps:**
1. **Attempted change** to LAW-type threshold flag:
   - Admin proposes threshold change via UI
   - System checks: `flag_type == LAW`
   - If LAW: raise `FlagLockedError` with migration guidance

2. **Migration process:**
   - Write migration patch (separate migration file, e.g., ` migrations/YYYYMMDD_migrate_thresholds.py`)
   - Patch includes: new threshold values, effective date, rollback plan
   - Run: `flask db migrate --model "threshold change patch"`
   - Run: `flask db upgrade` to apply
   - Audit log: migration event, actor=MIGRATION_SYSTEM, before/after, legal_basis

3. **Post-migration:**
   - New thresholds active
   - Config version incremented (separate from CONFIG-type versioning)
   - Notification: "Threshold migration applied per [Legal Basis], effective [date]"
   - All existing invoices: no retroactive change (audit integrity)

**Related Exceptions:** 
- `SystemSettingsError.FlagLockedError` (raised if admin attempts LAW change without migration)
- Existing pattern from SystemSettings: `InvalidRegimeError`, `ConfigVersionConflict`

**Triggers:** Admin attempts LAW-type threshold change

---

## Rules

### R-001: Invoice Status Prerequisite for Approval

**Rule:** Invoice can only be approved if current status = DRAFT.

**Detail:** 
- If status ∈ {APPROVED, REJECTED, CANCELLED, REPLACED} → raise ValueError
- Existing behavior in `Invoice.approve()` (src/domain/entities/invoice.py:118-119)
- New threshold check integrates BEFORE this status check or as part of it

**Exception Paths:** None - this is a hard constraint for data integrity

---

### R-002: Threshold Band Ascending Order

**Rule:** Threshold bands must be maintained in strictly ascending order: `T1.max_amount < T2.max_amount < T3.max_amount < T4.max_amount`.

**Detail:**
- System validation on config update (P-03 step 2)
- If not ascending → ValidationError: "Thresholds must be in ascending order: T1 < T2 < T3 < T4"
- Equal values not allowed (strict inequality)
- Minimum 5 bands required (T1-T5)

**Exception Paths:** None - system prevents non-ascending config

---

### R-003: Auto-Approval Condition (T1 with PO)

**Rule:** Invoices with `amount ≤ T1 ($500)` AND `po_matched = true` are auto-approved.

**Detail:**
- `po_matched` verified: invoice lines match existing purchase order in system
- If no PO reference → does not auto-approve, routes to manager (falls back to T2 path)
- If PO exists but lines don't match → routes to manager for verification
- Audit log: `action=auto_approve`, `po_matched=true/false`, `amount`

**Exception Paths:**
- Amount exactly $500 → included in T1 band (auto-approved with PO)
- Amount $501 → exceeds T1, routes to manager (T2 path)

---

### R-004: LAW-Type Flag Immutable Without Migration

**Rule:** LAW-type flag threshold changes require migration patch; cannot be changed via normal admin workflow.

**Detail:**
- Pattern from existing SystemSettings (AGENTS.md: "LAW-type flags immutable without migration")
- If admin attempts CONFIG-type vs LAW-type threshold change:
  - CONFIG-type: 1st approval (admin) → 2nd approval (chief accountant) → active
  - LAW-type: raise `FlagLockedError`, require separate migration patch (P-08)
- SystemChecks in `SystemSettingsService.update_config()` validate flag_type before proceeding

**Exception Paths:** Migration patch path (P-08) - authorized, tracked change

---

### R-005: Invoice Splitting Detection

**Rule:** System detects invoice splitting pattern: ≥2 invoices from same vendor within 24h, individual amounts under next threshold band, total exceeds that band.

**Detail:**
- Algorithm runs post-invoice-creation (real-time + 5-min batch)
- Pattern conditions:
  1. `COUNT(invoices) ≥ 2` from same `vendor_tax_id` within 24h window
  2. `ALL(individual_amount < next_band_max)` - e.g., all under $5K for T2
  3. `SUM(total_amount) > next_band_max` - e.g., total > $5K
- If all 3 conditions met → `splitting_events` record created, status='pending_review'
- Both invoices routed to CHIEF_ACCOUNTANT regardless of individual amounts
- Chief accountant can override with justification (audit records "splitting_override")
- If vendor has ≥3 splitting events in 30 days → auto-alert admin, recommend vendor review

**Exception Paths:**
- Single invoice from vendor → no splitting detection
- Invoices from different vendors → no splitting detection (even if same amount pattern)
- Invoices >24h apart → no splitting detection (timing window exceeded)
- Legitimate business reason → chief accountant overrides with written justification

---

### R-006: Delegation Expiry ≤ 30 Days

**Rule:** Delegation of authority period must not exceed 30 days.

**Detail:**
- System validates: `effective_to - effective_from ≤ 30 days` at delegation creation
- If > 30 days → ValidationError: "Delegation period exceeds 30-day maximum. Reduce period or request special authorization."
- Auto-expires on `effective_to` date
- Can be cancelled early by delegator
- No automatic extension - new delegation must be created if still needed

**Exception Paths:** Special authorization (admin override with documented reason) - rare, tracked

---

### R-007: Audit Log Append-Only Integrity

**Rule:** Audit log entries are append-only; no UPDATE or DELETE possible at database level.

**Detail:**
- Database triggers prevent modification of existing audit_log rows
- `checksum` field computed at entry creation, verified on access
- Retention policy: 2 years active in DB, then archive to cold storage (separate system)
- After 5 years: purge per company data retention policy (compliance with Vietnamese accounting archives rules)
- No soft-delete flags - entry either exists or doesn't (per Decree 70/2025 Appendix IA)

**Exception Paths:** None - integrity constraint enforced by DB schema + app logic

---

### R-008: Self-Approval Block

**Rule:** No user can approve an invoice they created (self-approval blocked by design).

**Detail:**
- System check: `invoice.creator_id == current_user_id` → raise ValidationError("Cannot approve own invoice")
- Applies to all approval paths: manager, chief accountant, director, admin
- If delegator needs own invoice approved → must designate delegate or have colleague approve
- Audit log: no entry created for blocked attempt (action not taken)

**Exception Paths:** None - design constraint, cannot be overridden

---

### R-009: Splitting Triggers Chief Accountant Review Regardless of Amount

**Rule:** When splitting detection fires, chief accountant review is triggered regardless of individual invoice amounts.

**Detail:**
- Normal threshold routing bypassed for splitting-detected invoices
- Both invoices routed to CHIEF_ACCOUNTANT even if individual amounts under T1 ($500)
- Chief accountant reviews consolidated total and pattern context
- Override possible with justification, but must be documented in audit log
- Deterrent effect: pattern learning across vendor history

**Exception Paths:**
- Chief accountant rejects both invoices → return to creators with reason
- Chief accountant approves with justification → "splitting_override" audit tag

---

### R-010: Config Re-Basing Documentation

**Rule:** Annual threshold re-basing must be documented in Re-Basing Report (T-006) and filed for audit compliance.

**Detail:**
- Report includes: old thresholds, new thresholds, invoice distribution analysis, rationale, 2nd approval signature
- Filed in company records per Vietnamese accounting archive requirements (Circular 99/2025)
- Report retained with other compliance documentation (2y active, 5y cold storage per P-05)
- Next review date documented in report

**Exception Paths:** Ad-hoc re-basing possible if business model changes >20% in invoice patterns (documented separately)

---

### R-011: Vietnamese Accounting Compliance (Circular 99/2025)

**Rule:** Approval workflow thresholds and processes must align with Circular 99/2025/TT-BTC requirements for documented accounting policies.

**Detail:**
- Company must have documented approval policy (this BRD + templates serve as policy artifact)
- Audit trails must be maintainable per Decree 70/2025/NĐ-CP Appendix IA (append-only logs)
- Thresholds must be consistently applied per company config (no arbitrary changes)
- MST validation on partners still applies (TaxId: `^\d{10}$` or `^\d{10}-\d{3}$`)
- E-invoice approval must follow GDT registration requirements (separate module, not in scope)
- Circular 99 removes rigid templates → but approval threshold policy must still be documented

**Exception Paths:** None - Vietnamese compliance is mandatory for operating in Vietnam

---

### R-012: PROD ENV Default Thresholds Operational

**Rule:** Default thresholds operational immediately in PROD; configurable via System Settings.

**Detail:**
- Defaults on deployment: T1=$500, T2=$5,000, T3=$25,000, T4=$100,000, T5=above
- No migration required for default installation
- Admin can propose changes (requires 2nd CA approval per P-03)
- LAW-type changes (if any) require migration patch (P-08)
- Existing tests pass (92 pass, 2 pre-existing failures Python 3.13 UUID, 14 pre-existing SQLAlchemy errors unchanged)

**Exception Paths:** Enterprise may customize thresholds via config; defaults serve as baseline

---

### R-013: Annual Re-Basing Reminder

**Rule:** System remembers last threshold re-basing date; notifies admin if not re-balanced in 365 days.

**Detail:**
- `companies` table or `system_config` table stores `last_re_basing_date`
- System cron job runs daily: if `NOW() - last_re_basing_date > 365 days` → notify admin
- Notification: "Threshold re-basing overdue (last: [date]), please review and adjust if needed"
- Does not block system operation but flags compliance risk
- Audit log entry: `action=re_basing_reminder`, `days_since_last`, `admin_notified`

**Exception Paths:** If re-basing report filed within same year → no notification needed (one-per-year policy)

---

## Summary of Rules

| Rule ID | Rule Title | Key Enforcement |
|---------|-----------|-----------------|
| R-001 | Invoice Status Prerequisite | `Invoice.approve()` ValueError if ≠ DRAFT |
| R-002 | Threshold Band Order | System validation on config update |
| R-003 | Auto-Approval T1+PO | `amount ≤ 500 AND po_matched → auto-approved` |
| R-004 | LAW-Type Immutable | `FlagLockedError` without migration |
| R-005 | Splitting Detection | ≥2 invoices same vendor 24h, total > band max |
| R-006 | Delegation ≤ 30 Days | System validation at creation |
| R-007 | Audit Append-Only | DB triggers + checksum enforcement |
| R-008 | Self-Approval Block | `creator_id != current_user_id` ValidationError |
| R-009 | Splitting → CA Review | Bypasses normal thresholds, routes to CHIEF_ACCOUNTANT |
| R-010 | Re-Basing Documentation | T-006 report, filed for audit |
| R-011 | VN Compliance (Circular 99) | Documented policy, audit trails, MST validation |
| R-012 | PROD Defaults Operational | Out-of-box: T1=$500, T2=$5K, T3=$25K, T4=$100K |
| R-013 | Re-Basing Reminder | 365-day notification to admin |