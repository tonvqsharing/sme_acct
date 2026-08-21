# Use Cases: Approval Workflows / Thresholds

## UC-001: Auto-Approve Low-Value Invoice (Under $500 with PO)

**Primary Actor:** AP Clerk / Manager  
**Trigger:** Invoice created with amount ≤ $500 and valid PO matched

### Preconditions
- Invoice in DRAFT status
- Invoice has at least one item with PO reference
- Company threshold config active (T1: $500 auto-approval band)

### Main Success Scenario
1. User creates invoice via UI → invoice initialized with status=DRAFT
2. `Invoice.add_item()` recalculates subtotal, vat_total, grand_total
3. System performs threshold check: `amount ≤ T1 ($500)`
4. PO matching verified: invoice lines match existing purchase order
5. **Happy Path:** System auto-sets status = APPROVED
6. Audit log entry created: `entity_type=invoice, entity_id=<id>, action=auto_approve, before_value=DRAFT, after_value=APPROVED, actor=system, timestamp`
7. Invoice proceeds to payment run immediately

### Alternative Paths
- **AP-001:** PO not matched → system routes to manager instead of auto-approving (falls back to UC-002)
- **AP-002:** Amount exactly $500 → included in T1 band (auto-approved)

### Exception Paths
- **EX-001:** Invoice amount $501 → exceeds T1, routes to manager (UC-002)
- **EX-002:** No PO reference on invoice → system does not auto-approve, routes to manager regardless of amount
- **EX-003:** Invoice already APPROVED or CANCELLED → raise ValueError("Hóa đơn đã được duyệt hoặc huỷ")

### Postconditions
- Invoice status = APPROVED
- Audit trail complete
- Invoice eligible for payment run

---

## UC-002: Manager Approves Medium-Value Invoice ($500 - $5,000)

**Primary Actor:** Manager  
**Trigger:** Invoice created with amount in T2 band, manager receives approval notification

### Preconditions
- Invoice in DRAFT status
- Amount: $500 < amount ≤ $5,000
- Manager role assigned in RBAC system
- Company threshold config active (T2: $5K manager band)

### Main Success Scenario
1. User creates invoice → status = DRAFT
2. Threshold check: `T1 < amount ≤ T2` → identifies T2 band
3. System routes approval request to manager via `@login_required + current_user.role == 'MANAGER'` check
4. Manager receives notification (email/HTMX in UI) with invoice details
5. Manager reviews: invoice number, amount, vendor, line items, PO match
6. Manager clicks "Approve" → status changes DRAFT → APPROVED
7. Audit log: `action=approve, approver=MANAGER, invoice_id, amount, timestamp`
8. Invoice proceeds to payment run

### Alternative Paths
- **AP-003:** Manager clicks "Reject" → status changes DRAFT → REJECTED, invoice returns to creator with reason
- **AP-004:** Manager delegates approval to deputy → delegation records update, deputy approves

### Exception Paths
- **EX-001:** Manager not authorized (RBAC check fails) → raise PermissionError("Manager role required for invoice approval")
- **EX-002:** Invoice amount $5,001 → exceeds T2, routes to chief accountant (UC-003)
- **EX-003:** Manager attempts self-approval on own invoice → system blocks; raise ValidationError("Cannot approve own invoice")
- **EX-004:** Invoice splitting detected (2 invoices from same vendor within 24h totaling >$5K) → flag for chief accountant (EX-005 in UC-005)

### Postconditions
- Invoice status = APPROVED (if approved) or REJECTED (if rejected)
- Audit trail complete
- Manager's approval count incremented

---

## UC-003: Chief Accountant Approves High-Value Invoice ($5,000 - $25,000)

**Primary Actor:** Chief Accountant  
**Trigger:** Invoice created with amount in T3 band, chief accountant receives approval notification

### Preconditions
- Invoice in DRAFT status
- Amount: $5,000 < amount ≤ $25,000
- CHIEF_ACCOUNTANT role assigned in RBAC system
- Company threshold config active (T3: $25K chief accountant band)

### Main Success Scenario
1. User creates invoice → status = DRAFT
2. Threshold check: `T2 < amount ≤ T3` → identifies T3 band
3. System routes approval request to chief accountant via `@login_required + current_user.role == 'CHIEF_ACCOUNTANT'` check
4. Chief accountant receives notification with full invoice context
5. Chief accountant reviews: invoice number, amount, vendor, tax compliance, overall financial impact
6. Chief accountant clicks "Approve" → status changes DRAFT → APPROVED
7. Audit log: `action=approve, approver=CHIEF_ACCOUNTANT, invoice_id, amount, timestamp`
8. Invoice proceeds to payment run

### Alternative Paths
- **AP-005:** Chief accountant clicks "Reject" → status DRAFT → REJECTED
- **AP-006:** Chief accountant delegates to director (if unavailable) → delegation in effect

### Exception Paths
- **EX-001:** Chief accountant not authorized → PermissionError (should not happen with proper RBAC)
- **EX-002:** Invoice amount $25,001 → exceeds T3, routes to director (UC-004)
- **EX-003:** Splitting detection from UC-001/UC-002 triggers → chief accountant already reviewing, this invoice consolidated into splitting event
- **EX-004:** Attempt to approve invoice with status ≠ DRAFT → ValueError (existing behavior in `Invoice.approve()`)

### Postconditions
- Invoice status = APPROVED
- Audit trail complete with chief accountant sign-off
- Chief accountant's approval count incremented
- Invoice eligible for payment run

---

## UC-004: Director Approves Executive-Value Invoice ($25,000 - $100,000)

**Primary Actor:** Director  
**Trigger:** Invoice created with amount in T4 band, director receives approval notification

### Preconditions
- Invoice in DRAFT status
- Amount: $25,000 < amount ≤ $100,000
- DIRECTOR role assigned in RBAC system
- Company threshold config active (T4: $100K director band)

### Main Success Scenario
1. User creates invoice → status = DRAFT
2. Threshold check: `T3 < amount ≤ T4` → identifies T4 band
3. System routes approval request to director via `@login_required + current_user.role == 'DIRECTOR'` check
4. Director receives notification with executive-level context
5. Director reviews: strategic impact, budget alignment, multi-entity considerations
6. Director clicks "Approve" → status changes DRAFT → APPROVED
7. Audit log: `action=approve, approver=DIRECTOR, invoice_id, amount, timestamp`
8. Invoice proceeds to payment run

### Alternative Paths
- **AP-007:** Director clicks "Reject" → status DRAFT → REJECTED

### Exception Paths
- **EX-001:** Director not authorized → PermissionError
- **EX-002:** Invoice amount > $100K → routes to ADMIN/Board (UC-005)
- **EX-003:** Emergency approval bypass → requires separate ADMIN approval with full audit

### Postconditions
- Invoice status = APPROVED
- Executive audit trail complete
- Invoice proceeds to payment run

---

## UC-005: Admin/Board Approves Ultra-Value Invoice (>$100,000)

**Primary Actor:** Admin / Board Member  
**Trigger:** Invoice created with amount exceeding T4 band

### Preconditions
- Invoice in DRAFT status
- Amount: amount > $100,000
- ADMIN or BOARD role assigned in RBAC system
- Company threshold config active (T5: above $100K)

### Main Success Scenario
1. User creates invoice → status = DRAFT
2. Threshold check: `amount > T4` → identifies T5 band
3. System routes approval request to ADMIN/Board via `@login_required + current_user.role in ('ADMIN', 'BOARD')` check
4. Admin/Board receives notification with full financial context
5. Review: materiality, strategic alignment, board policy compliance
6. Admin clicks "Approve" → status changes DRAFT → APPROVED
7. Audit log: `action=approve, approver=ADMIN, invoice_id, amount, timestamp, special_justification`
8. Invoice proceeds to payment run

### Alternative Paths
- **AP-008:** Admin/Board clicks "Reject" → status DRAFT → REJECTED

### Exception Paths
- **EX-001:** Insufficient RBAC permissions → access denied
- **EX-002:** Company without T5 configured → use defaults; prompt for config update
- **EX-003:** Emergency board meeting not scheduled → deferred to next board cycle

### Postconditions
- Invoice status = APPROVED
- High-level audit trail with board sign-off
- Invoice proceeds to payment run

---

## UC-006: Invoice Splitting Detection and Prevention

**Primary Actor:** System (automated) / Chief Accountant (review)  
**Trigger:** Multiple invoices from same vendor/requester within threshold-bypass pattern

### Preconditions
- Invoice created in DRAFT status
- Vendor has existing invoices in system

### Main Success Scenario
1. User creates Invoice INV-001: amount $4,800 (under T2 $5K threshold)
2. Within 24h, same vendor creates Invoice INV-002: amount $4,700 (also under T2)
3. System's splitting detection algorithm runs post-creation:
   - Check: same vendor_tax_id, within 24h window, individual amounts under threshold
   - Calculate: total $9,500 exceeds T2 threshold
4. System flags splitting event:
   - Create `splitting_events` record
   - Route both invoices to chief accountant regardless of individual amounts
5. Chief accountant reviews consolidated spend
6. Chief accountant approves with justification → audit log records "splitting override"
7. Both invoices proceed to payment with consolidated approval

### Alternative Paths
- **AP-009:** No splitting pattern detected (invoices from different vendors or >24h apart) → normal approval path

### Exception Paths
- **EX-005:** Splitting detected but vendor is approved and spend legitimate → chief accountant overrides with written justification, audit log: "splitting_override, justification_text"
- **EX-006:** Splitting detection false positive (legitimate business reason for split timing) → system documents exception, chief accountant signs off
- **EX-007:** Splitting event older than 30 days → auto-resolve, archived in audit log

### Postconditions
- Both invoices routed to chief accountant
- Splitting event recorded in audit log
- Consolidated approval recorded
- Pattern learning: system remembers vendor splitting history

---

## UC-007: Delegation of Authority

**Primary Actor:** Chief Accountant (delegator) / Delegate  
**Trigger:** Approver unavailable (leave, absence), designates stand-in

### Preconditions
- Chief accountant has pending approvals
- Delegator is chief accountant role
- Delegate has appropriate RBAC role (CHIEF_ACCOUNTANT or ADMIN)

### Main Success Scenario
1. Chief accountant identifies will be unavailable (leave, travel)
2. Chief accountant designates delegate via UI/system
3. System records delegation:
   - delegator_id = chief_accountant_id
   - delegate_id = deputy_ chief_accountant_id
   - effective_from = today
   - effective_to = today + 30 days (max)
   - scope = "all_pending_approvals" or "specific_band"
   - reason = "On maternity leave / Annual leave"
4. System notifications: delegate receives all chief accountant's pending approval notifications
5. Delegate approves/rejects on behalf of chief accountant
6. Audit log: `action=approve, approver=DELEGATE (on behalf of CHIEF_ACCOUNTANT), invoice_id, amount, timestamp`
7. Upon chief accountant's return: delegation expires, original approver resumes

### Alternative Paths
- **AP-010:** No delegation set → approvals accumulate, system alerts admin after 48h

### Exception Paths
- **EX-008:** Delegation period > 30 days → system rejects, prompt to renew or adjust
- **EX-009:** Delegate lacks sufficient RBAC role → PermissionError ("Insufficient approval authority")
- **EX-010:** Delegator returns early → system cancels delegation early, original approver resumes
- **EX-011:** Delegator attempts to approve own delegated approvals → system blocks; only delegate can act

### Postconditions
- Pending approvals handled during delegator's absence
- Complete audit trail with delegation markers
- Original approver resumes after delegation expiry

---

## UC-008: Threshold Configuration Update

**Primary Actor:** Admin / Chief Accountant  
**Trigger:** Admin proposes new threshold matrix; requires approval workflow

### Preconditions
- Admin authenticated in system
- Company has existing threshold config (or using defaults)
- Proposed changes within reasonable bounds

### Main Success Scenario (CONFIG-type flag)
1. Admin proposes new threshold config via System Settings update
2. System validates: thresholds must be ascending (T1 < T2 < T3 < T4)
3. If CONFIG-type flag: 
   - 1st approval: Admin submits change
   - 2nd approval: Chief Accountant must approve
   - System increments `config_version`
   - Audit log: before/after values, config_version, actors
4. If LAW-type flag: raise FlagLockedError, require migration patch
5. Cache invalidation: all pending invoices re-evaluated against new thresholds
6. Notify: admin and chief accountant of config change completion

### Alternative Paths
- **AP-011:** Changes rejected at 1st approval → config unchanged, audit log records rejection

### Exception Paths
- **EX-012:** Proposed thresholds not ascending → ValidationError("Thresholds must be in ascending order: T1 < T2 < T3 < T4")
- **EX-013:** LAW-type flag change attempt → FlagLockedError with migration guidance
- **EX-014:** 2nd approval not received within 7 days → proposal expires, admin must resubmit

### Postconditions
- New threshold config active (if 2nd approval received)
- Audit trail complete with config_version history
- Pending invoices reevaluated

---

## UC-009: Annual Threshold Re-Baselining

**Primary Actor:** Admin  
**Trigger:** Annual review of threshold matrix against actual invoice distribution

### Preconditions
- 12 months of invoice data accumulated
- Admin initiates re-baselining process

### Main Success Scenario
1. Admin reviews 12-month invoice distribution data
2. Admin proposes adjusted thresholds to better match current volume
3. Threshold config update process (UC-008) initiates
4. 2nd approval (chief accountant) received
5. New thresholds active
6. Audit log: re-basing event, old thresholds archived, new thresholds active
7. Notification: all stakeholders informed of new thresholds

### Alternative Paths
- **AP-012:** No changes needed → maintain existing thresholds, document decision in audit log

### Exception Paths
- **EX-015:** Insufficient data (less than 3 months) → defer re-baselining, revisit in quarter
- **EX-016:** Drastic shift in business model → recommend interim config change outside annual cycle

### Postconditions
- Thresholds re-baselined to current business reality
- Audit trail of re-basing decision
- Stakeholder communication complete

---

## UC-010: Audit Trail Review for Approval Compliance

**Primary Actor:** Auditor / Internal Audit  
**Trigger:** Periodic compliance review of approval workflow

### Preconditions
- Auditor has READ access to audit logs
- Review period defined (e.g., quarterly, annually)

### Main Success Scenario
1. Auditor queries audit logs: `entity_type=invoice, action IN ('auto_approve', 'approve', 'splitting_override')`
2. Auditor reviews: threshold checks performed, approvers appropriate, no skipping
3. Auditor identifies: any approvers consistently rubber-stamping, threshold bypass patterns, splitting events
4. Auditor generates compliance report
5. Findings documented; recommendations issued if gaps identified

### Alternative Paths
- **AP-013:** No issues found → report documents "compliant, no findings"
- **AP-014:** Issues found → report with specific recommendations (e.g., "increase T2 threshold", "investigate vendor X splitting")

### Postconditions
- Compliance report filed
- Action items documented if findings identified
- Audit log integrity verified (append-only, no deletions)

---

## Summary of Use Cases

| UC-ID | Title | Primary Actor | Key Flow |
|-------|-------|--------------|----------|
| UC-001 | Auto-Approve Low-Value Invoice | AP Clerk | Threshold T1 → auto-approved |
| UC-002 | Manager Approves Medium Invoice | Manager | Threshold T2 → manager approval |
| UC-003 | Chief Accountant Approves High Invoice | Chief Accountant | Threshold T3 → CA approval |
| UC-004 | Director Approves Executive Invoice | Director | Threshold T4 → director approval |
| UC-005 | Admin/Board Approves Ultra Invoice | Admin/Board | Threshold T5+ → executive approval |
| UC-006 | Invoice Splitting Detection | System | Pattern detection → chief accountant |
| UC-007 | Delegation of Authority | Chief Accountant / Delegate | Temporary authority transfer |
| UC-008 | Threshold Configuration Update | Admin/CA | Config update → 2nd approval → active |
| UC-009 | Annual Threshold Re-Baselining | Admin | 12-month review → adjust thresholds |
| UC-010 | Audit Trail Compliance Review | Auditor | Audit log review → compliance report |