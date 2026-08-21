# User Journeys: Invoice Approval Workflows

## UJ-001: Standard Invoice Creation and Approval (SME, $3,500 invoice)

**User Role:** Accountant / AP Clerk  
**Company Size:** Small - using default thresholds  
**Invoice Amount:** $3,500 (within T2: $500-$5,000 manager band)

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User logs into accounting app | Dashboard displayed, company selector (if multi-company) |
| 2 | User navigates to "Create Invoice" | Invoice creation form displayed |
| 3 | User enters invoice details: number, date, vendor, amount $3,500 | Form fields populated |
| 4 | User adds line items (products/services, quantities, prices) | `Invoice.add_item()` recalculates: subtotal=$3,500, vat_total, grand_total |
| 5 | User saves invoice → status = DRAFT | Invoice stored in DB, status=DRAFT |
| 6 | System performs threshold check: `$500 < $3,500 ≤ $5,000` → T2 band | Threshold service evaluates band |
| 7 | System routes approval request to manager | Notification sent to manager's dashboard/email |
| 8 | Manager logs in → sees pending approvals count | Pending approvals badge: 1 |
| 9 | Manager reviews invoice → clicks "Approve" | `@login_required + current_user.role == 'MANAGER'` check enforces RBAC |
| 10 | System changes status DRAFT → APPROVED | `Invoice.approve()` called, status updated |
| 11 | Audit log entry created | `entity_type=invoice, action=approve, approver=MANAGER, amount=$3,500` |
| 12 | Invoice proceeds to payment run | Ready for next AP cycle |

### Outcome
- Invoice approved by manager
- Audit trail complete
- Invoice eligible for payment
- Manager's approval count: +1

---

## UJ-002: High-Value Invoice Approval (Chief Accountant, $22,000 invoice)

**User Role:** Accountant / AP Clerk  
**Company Size:** Medium - using default thresholds  
**Invoice Amount:** $22,000 (within T3: $5,000-$25,000 chief accountant band)

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User logs into accounting app | Dashboard displayed |
| 2 | User creates invoice for $22,000 with 3 line items | Invoice created, status=DRAFT |
| 3 | `Invoice.add_item()` recalculates totals | subtotal=$22,000, vat_total calculated, grand_total |
| 4 | System threshold check: `$5,000 < $22,000 ≤ $25,000` → T3 band | Threshold service identifies T3 |
| 5 | Approval request routed to chief accountant | Notification: "22 pending approvals from accountants" |
| 6 | Chief accountant logs in → sees "Chief Accountant approvals" section | Badge: 1 high-value invoice pending |
| 7 | Chief accountant reviews invoice details | Vendor, tax compliance, overall impact displayed |
| 8 | Chief accountant clicks "Approve" | `@login_required + current_user.role == 'CHIEF_ACCOUNTANT'` check enforces RBAC |
| 9 | System changes status DRAFT → APPROVED | `Invoice.approve()` updates status |
| 10 | Audit log: `action=approve, approver=CHIEF_ACCOUNTANT, amount=$22,000` | Immutable audit record created |
| 11 | Invoice proceeds to payment run | Added to next payment batch |

### Outcome
- Chief accountant approves high-value invoice
- Full executive audit trail
- Invoice eligible for payment
- Compliance with Vietnamese accounting regulations (Circular 99/2025)

---

## UJ-003: Ultra-Value Invoice (Director Approval, $85,000 invoice)

**User Role:** Senior Accountant / Finance Manager  
**Company Size:** Enterprise - using default thresholds  
**Invoice Amount:** $85,000 (within T4: $25,000-$100,000 director band)

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User logs into accounting app | Dashboard with enterprise features |
| 2 | User creates $85,000 invoice with detailed line items | Invoice created, status=DRAFT |
| 3 | System threshold check: `$25,000 < $85,000 ≤ $100,000` → T4 band | Threshold service identifies T4 |
| 4 | Approval request routed to director | Notification with executive context |
| 5 | Director reviews: strategic alignment, budget impact, multi-entity considerations | Full invoice context displayed |
| 6 | Director clicks "Approve" | `@login_required + current_user.role == 'DIRECTOR'` check enforces RBAC |
| 7 | System changes status DRAFT → APPROVED | Status updated in DB |
| 8 | Audit log: `action=approve, approver=DIRECTOR, amount=$85,000, special_justification` | Records executive sign-off |
| 9 | Invoice proceeds to payment run with director sign-off | High-value payment batch |

### Outcome
- Director approves executive-value invoice
- Strategic oversight documented
- Audit trail at director level
- Invoice proceeds to payment

---

## UJ-004: Auto-Approval Low-Value Invoice (Under $500)

**User Role:** AP Clerk  
**Company Size:** Any - using default thresholds  
**Invoice Amount:** $350 (within T1: ≤$500 auto-approval band)

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User creates invoice for $350 with valid PO reference | Invoice created, status=DRAFT |
| 4 | User adds line items, saves → status=DRAFT | `Invoice.add_item()` recalculates |
| 5 | System threshold check: `$350 ≤ $500` → T1 band | Threshold service: auto-approval condition met |
| 6 | PO matching verification: invoice lines match existing PO | PO check: matched ✓ |
| 7 | **Happy Path:** System auto-sets status = APPROVED (no human approval needed) | `Invoice.approve()` called internally |
| 8 | Audit log: `action=auto_approve, amount=$350, po_matched=true` | System auto-approval recorded |
| 9 | Invoice immediately proceeds to payment run | No approval delay |

### Alternative Path
- **If no PO reference:** System routes to manager (UC-002 path) instead of auto-approving

### Outcome
- Invoice auto-approved
- Zero approval time for low-value transactions
- Audit trail records auto-approval
- AP clerk time saved on routine transactions

---

## UJ-005: Invoice Splitting Detection and Consolidated Approval

**User Role:** Accountant / AP Clerk  
**Trigger:** Two invoices from same vendor within 24h to bypass thresholds  
**Invoices:** INV-001 ($4,800) and INV-002 ($4,700), same vendor, within 24h

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User creates Invoice INV-001 for $4,800 (under T2 $5K threshold) | Invoice created, status=DRAFT, system records creation timestamp |
| 2 | Within 24h, same vendor creates Invoice INV-002 for $4,700 (also under T2) | INV-002 created, status=DRAFT |
| 3 | System's splitting detection algorithm runs post-INV-002 creation | Checks: same vendor_tax_id, within 24h window, individual amounts under threshold |
| 4 | Pattern detected: total $9,500 exceeds T2 threshold | System creates splitting event record |
| 5 | Both invoices flagged → routed to chief accountant | Bypasses manager approval for both invoices |
| 6 | Chief accountant receives notification: "Splitting detection: 2 invoices, vendor XYZ, total $9,500" | Chief accountant review triggered |
| 7 | Chief accountant reviews both invoices together | Context: "2 invoices from same vendor, suspected splitting to bypass $5K threshold" |
| 8 | Chief accountant approves with justification | `action=approve, approver=CHIEF_ACCOUNTANT, splitting_override=true` |
| 9 | Audit log: splitting event recorded + override reason | Immutable: "splitting detected, total $9,500, approved with justification" |
| 10 | Both invoices proceed to payment | Consolidated approval, payment batch includes both |

### Alternative Path
- If chief accountant rejects: both invoices REJECTED, vendor notified, pattern noted for future

### Outcome
- Splitting pattern detected and prevented
- Chief accountant oversight enforced
- Audit trail complete with splitting markers
- Deterrent effect: future splitting attempts more visible

---

## UJ-006: Delegation of Authority (Chief Accountant on Leave)

**User Role:** Chief Accountant (delegator) / Deputy Chief Accountant (delegate)  
**Trigger:** Chief accountant unavailable for 2-week period

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Chief accountant identifies 2-week absence (maternity/paternity leave) | Notes absence in system |
| 2 | Chief accountant designates deputy as delegate via UI | Delegation form submitted |
| 3 | System records delegation: | `approval_delegations` table created: |
|   | - delegator_id = chief_accountant_id | - delegator: chief_accountant |
|   | - delegate_id = deputy_ca_id | - delegate: deputy_chief_accountant |
|   | - effective_from = today | - start date |
|   | - effective_to = today + 14 days | - end date (within 30-day max) |
|   | - scope = "all_pending_approvals" | - covers all pending |
|   | - reason = "On maternity leave" | - documented reason |
| 4 | System notifications: deputy receives all chief accountant's pending approval alerts | Badge on deputy's dashboard: "5 pending (CA's delegate)" |
| 5 | Deputy reviews and approves invoices on behalf | `@login_required + current_user.role == 'CHIEF_ACCOUNTANT'` check but delegation flag overrides |
| 6 | Audit log: `action=approve, approver=DELEGATE (on behalf of CHIEF_ACCOUNTANT)` | Records delegation in audit |
| 7 | After 14 days: delegation expires automatically | Original chief accountant resumes approvals |
| 8 | Any remaining approvals: revert to chief accountant | System: "delegation expired, returning to original approver" |

### Alternative Path
- **If chief accountant returns early:** System cancels delegation early, original approver resumes

### Exception Path
- **If delegation period > 30 days:** System rejects new delegation, prompt to renew or adjust

### Outcome
- Pending approvals handled during absence
- No bottlenecks in approval workflow
- Complete audit trail with delegation markers
- Chief accountant resumes control after return

---

## UJ-007: Threshold Configuration Update (2nd Approval Required)

**User Role:** Admin (proposes) / Chief Accountant (approves 2nd)  
**Trigger:** Admin wants to adjust thresholds from defaults

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Admin logs in → navigates to "System Settings → Thresholds" | Current threshold matrix displayed |
| 2 | Admin proposes new thresholds: T1=$200, T2=$3,000, T3=$15,000, T4=$50,000 | Config update form submitted |
| 3 | System validates: thresholds must be ascending | Validation: $200 < $3,000 < $15,000 < $50,000 ✓ |
| 4 | Since CONFIG-type flag: 1st approval required | System increments draft_config_version, records "pending_1st_approval" |
| 5 | Audit log: before values, proposed after values, actor=ADMIN, config_version incremented | Immutable record of proposal |
| 6 | Admin submits → chief accountant notified of pending 2nd approval | Email/notification to chief accountant |
| 7 | Chief accountant reviews proposed thresholds | Reviews for business alignment, compliance |
| 8 | Chief accountant clicks "Approve 2nd" | `SystemSettingsService.update_config()` performs 2nd approval check |
| 9 | System: config_version incremented, new thresholds active, cache invalidated | All pending invoices re-evaluated against new thresholds |
| 10 | Audit log: after values, actors (ADMIN submitted, CHIEF_ACCOUNTANT approved), config_version=5 | Complete audit trail |
| 11 | Notification: admin and stakeholders informed | "Thresholds updated effective immediately" |

### Alternative Path
- **If chief accountant rejects at 2nd approval:** Config unchanged, audit log records rejection, admin must resubmit

### Exception Path
- **If LAW-type flag attempted:** `FlagLockedError` raised, migration patch required instead

### Outcome
- New thresholds active after 2nd approval
- Full audit trail of config change
- Pending invoices automatically reevaluated
- Compliance with existing system settings patterns

---

## UJ-008: Annual Threshold Re-Baselining

**User Role:** Admin  
**Trigger:** 12-month review cycle, typically at fiscal year start

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Admin reviews 12 months of invoice distribution data | Exported report: invoice count and amounts by threshold band |
| 2 | Admin identifies: current T2 ($5K) handles 65% of invoices, but new business adds high-value invoices | Analysis completed |
| 3 | Admin proposes adjusted thresholds: T1=$300, T2=$4,000, T3=$20,000, T4=$75,000 | Proposal submitted via UC-008 path |
| 4 | 2nd approval (chief accountant) received within 7 days | Config updated, new thresholds active |
| 5 | Cache invalidation: all pending invoices reevaluated | Old thresholds archived in audit log |
| 6 | Notification: all stakeholders informed of new thresholds | Email to admin, chief accountant, AP team |
| 7 | Audit log: "re-basing event, old T1=$500→new T1=$300, date=2026-01-15" | Permanent record of re-basing decision |

### Outcome
- Thresholds aligned with current business reality
- Data-driven decision documented
- Audit trail of re-basing process
- Improved approval efficiency matching actual spend patterns

---

## UJ-009: Audit Compliance Review (Internal Audit)

**User Role:** Internal Auditor  
**Trigger:** Quarterly compliance review

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Auditor accesses audit logs module | Filter options: entity_type=invoice, date range, action types |
| 2 | Auditor queries: `action IN ('auto_approve', 'approve', 'splitting_override')` for last quarter | List of all approval actions displayed |
| 3 | Auditor reviews: threshold checks performed, approver roles correct | Spreadsheet or UI grid of all events |
| 4 | Auditor identifies patterns: "Manager auto-approved 200/200 invoices without PO check" | Finding documented |
| 5 | Auditor generates compliance report with findings/recommendations | Report PDF generated |
| 6 | Report distributed to: admin, chief accountant, board (if material) | Distribution list notified |
| 7 | Action items tracked: "Increase T2 threshold", "Investigate vendor X splitting" | Tasks created in system |

### Alternative Path
- **If no issues found:** Report documents "compliant, no findings" with supporting statistics

### Outcome
- Compliance verification complete
- Findings documented if any
- Action items tracked for resolution
- Audit trail integrity verified (append-only, no deletions possible)

---

## UJ-010: Self-Approval Block Attempt

**User Role:** Any user attempting to approve their own invoice  
**Trigger:** User tries to approve invoice they created

### Journey Steps

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User creates invoice for $3,500 | Invoice in DRAFT status, creator=user_id |
| 2 | User attempts to approve own invoice via UI | System check: `invoice.creator_id == current_user_id` |
| 3 | System blocks approval | `ValidationError("Cannot approve own invoice")` raised |
| 4 | Invoice remains in DRAFT status | No status change |
| 5 | User must delegate or have colleague approve | Alternative path required |

### Outcome
- Self-approval prevented by design
- Maintains approval integrity
- Audit log not created (no approval action taken)
- User redirected to proper approval path (delegate or colleague)

---

## Summary of User Journeys

| UJ-ID | Title | Key User Role | Primary Outcome |
|-------|-------|--------------|-----------------|
| UJ-001 | Standard Invoice Approval | Accountant/AP Clerk | Manager-approved, $3.5K invoice |
| UJ-002 | Chief Accountant Approval | Chief Accountant | CA-approved, $22K invoice |
| UJ-003 | Director Approval | Director | Director-approved, $85K invoice |
| UJ-004 | Auto-Approval Low-Value | AP Clerk | Auto-approved, $350 invoice (with PO) |
| UJ-005 | Splitting Detection | Accountant/AP Clerk | Pattern caught, chief accountant review |
| UJ-006 | Delegation of Authority | CA / Deputy CA | Temporary authority transfer during absence |
| UJ-007 | Threshold Configuration | Admin/CA | 2nd approval required, thresholds updated |
| UJ-008 | Annual Re-Baselining | Admin | Thresholds aligned with business reality |
| UJ-009 | Audit Compliance Review | Internal Auditor | Compliance verification, findings if any |
| UJ-010 | Self-Approval Block | Any user | Design prevents self-approval, integrity maintained |