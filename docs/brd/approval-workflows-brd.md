# BRD: Approval Workflows / Thresholds

## Objective

Define and implement dollar-value approval thresholds and approval paths for invoices and journals in the Vietnamese SME accounting application. This system enables auto-routing of invoices based on amount, enforces delegation of authority, and ensures compliance with Vietnamese accounting regulations (Circular 99/2025/TT-BTC, Decree 70/2025/NĐ-CP, GDT e-invoicing requirements).

**Success Criteria:**
- Invoices above dollar thresholds auto-route to designated approvers per approved matrix
- System enforces Delegation of Authority (DoA) policy without manual intervention
- Audit trail records all approval actions, threshold checks, and exceptions
- Operates in PROD environment with Vietnamese MST/tax compliance
- Re-baseline thresholds annually against invoice distribution
- No executive approver bottleneck for routine invoices (< $5K typical)

## Scope

**In Scope:**
- Dollar-value approval thresholds for invoices (sales and purchase)
- Approval path matrix by amount bands
- Delegation of Authority (DoA) management
- Audit logging of all approval actions
- Integration with existing Invoice `approve()` method
- RBAC integration with `@casbin_required` decorators
- Configurable via System Settings (CONFIG-type flags)
- Templates for approval requests, matrices, DoA

**Out of Scope:**
- Multi-company consolidation logic (research report flags 7 critical gaps)
- System Settings REST API (deferred to next version)
- UI-only auth — backend service methods must enforce RBAC
- E-invoice signing workflow (separate e-invoice module)

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | System shall maintain an approval threshold matrix mapping dollar amounts to required approver roles | High |
| FR-002 | Invoices with amount ≤ threshold A shall auto-approve by manager role | High |
| FR-003 | Invoices with amount > threshold A and ≤ threshold B shall require chief accountant approval | High |
| FR-004 | Invoices with amount > threshold B shall require director/admin approval | High |
| FR-005 | System shall detect invoice splitting (multiple invoices from same vendor/requester within 24h to bypass thresholds) | High |
| FR-006 | Shall maintain audit log of: invoice ID, amount, threshold check result, approver, timestamp, reason | High |
| FR-007 | Shall support configurable thresholds per company (one CompanyConfig per company) | High |
| FR-008 | Shall integrate with existing `@casbin_required` decorator for RBAC enforcement | High |
| FR-009 | Shall allow delegation of approval authority when approver is unavailable | Medium |
| FR-010 | Shall support multiple threshold bands (typical: $0-5K, $5K-25K, $25K-100K, $100K+) | Medium |
| FR-011 | Shall validate threshold config on CompanyConfig update (LAW-type flags require migration) | High |
| FR-012 | Shall operate in PROD environment with default thresholds; configurable for enterprise | High |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | Threshold config updates require 2nd approval for CONFIG-type flags (per existing system settings pattern) | High |
| NFR-002 | System shall not allow LAW-type flag threshold changes without migration patch | High |
| NFR-003 | Audit logs shall be append-only (REVOKE DELETE after 2y cold storage per P-05) | High |
| NFR-004 | Response time for threshold check < 200ms per invoice | Medium |
| NFR-005 | Default thresholds: $500 (auto-approve with PO), $5K (manager), $25K (chief accountant), $100K (director) | Medium |

## Approval Workflow Design

### Threshold Matrix (Default - configurable per company)

| Band | Maximum Amount | Approver Role | Action |
|------|---------------|---------------|--------|
| T1 | $500 | Auto-approval (if PO matched) | Auto-approved |
| T2 | $5,000 | Manager (PHÒNG/GĐ) | Requires manager sign-off |
| T3 | $25,000 | Chief Accountant (TRƯỞNG KỊ TOÁN) | Requires CHIEF_ACCOUNTANT approval |
| T4 | $100,000 | Director (GIÁM ĐỒNG) | Requires DIRECTOR approval |
| T5 | Above | ADMIN/BOARD | Requires executive sign-off |

### Approval Path Logic

```
Invoice Amount → Check Threshold Matrix → Determine Approver Role → Route for Approval → Record Audit Log
```

### RBAC Integration

- **Manager** role: `@casbin_required('MANAGER')` for T2 thresholds
- **Chief Accountant** role: `@casbin_required('CHIEF_ACCOUNTANT')` for T3 thresholds  
- **Director** role: `@casbin_required('DIRECTOR')` for T4+ thresholds
- **AUDITOR** role: Read-only, no approval capability
- Default role hierarchy: ACCOUNTANT → CHIEF_ACCOUNTANT → ADMIN → DIRECTOR (per rbac_policy.csv)

## User Journeys

### J-001: Manager Approves Routine Invoice (Under $5K)

1. User creates invoice in DRAFT status
2. Invoice amount $3,200 → threshold check: T2 ($5K)
3. System routes to manager for approval
4. Manager receives notification → reviews invoice → clicks "Approve"
5. System changes status from DRAFT → APPROVED
6. Audit log entry: invoice_id, $3,200, manager, approve, timestamp
7. Invoice proceeds to payment run

### J-002: Chief Accountant Approves High-Value Invoice ($25K)

1. User creates invoice in DRAFT status
2. Invoice amount $28,500 → threshold check: T3 ($25K)
3. System routes to chief accountant for approval
4. Chief accountant reviews → clicks "Approve"
5. System changes status DRAFT → APPROVED
6. Audit log entry: invoice_id, $28,500, chief_accountant, approve, timestamp
7. Invoice proceeds to payment run

### J-003: Invoice Splitting Detection

1. User creates invoice INV-001 for $4,800 (under $5K manager threshold)
2. Within 24h, same vendor creates INV-002 for $4,700 (also under threshold)
3. System detects pattern: 2 invoices from same vendor within 24h, total $9,500
4. System flags for review → routes to chief accountant regardless of individual amounts
5. Audit log: splitting detection event, both invoice IDs, total amount, flagged reason
6. Chief accountant reviews and approves total spend

### J-004: Delegation of Authority

1. Chief accountant is unavailable (on leave)
2. System identifies pending approvals for chief accountant
3. Chief accountant designates delegate via UI → selects deputy chief accountant
4. System records delegation: delegator, delegate, effective date, expiry date
5. Delegate receives notifications for chief accountant's pending approvals
6. Delegate approves on behalf → audit log records: "approved_by_delegate"
7. Upon chief accountant's return, delegation expires

## Data Flow Design

```
[Create Invoice] → [add_item → recalculate] → [status = DRAFT]
      │
      ├──→ [threshold_check] ──┐
      │                       │
      │                       └──→ [amount ≤ T1] → Auto-approved → [APPROVED]
      │                               │
      │                               └──→ [T1 < amount ≤ T2] → Route to Manager
      │                                           │
      │                                           └──→ [Manager approves] → [APPROVED]
      │
      └──→ [T2 < amount ≤ T3] → Route to Chief Accountant
                              │
                              └──→ [Chief Accountant approves] → [APPROVED]
      ...
                          
[Audit Log Write] ←──┘ (append-only, entity_type=invoice, entity_id=..., action=approve/threshcheck/splitting)
```

## Rules

| Rule ID | Rule | Exception Path |
|---------|------|----------------|
| R-001 | Invoice can only be approved if status = DRAFT | If not DRAFT, raise ValueError (existing behavior) |
| R-002 | Invoice amount ≤ T1 ($500) → auto-approval if PO matched | If no PO, route to manager anyway |
| R-003 | Threshold config changes for CONFIG-type flags require 2nd approval | 1st approver submits, CHIEF_ACCOUNTANT approves |
| R-004 | LAW-type flag threshold changes require migration patch | System raises FlagLockedError |
| R-005 | Invoice splitting detection: >1 invoice from same vendor within 24h, total exceeds next threshold | Flag for chief accountant review |
| R-006 | Delegation must have expiry date ≤ 30 days | If longer, system rejects |
| R-007 | Audit log entries are immutable after creation | No delete; archive after 2y |
| R-008 | Default thresholds are company-configurable but must maintain ascending order | T1 < T2 < T3 < T4 |
| R-009 | Splitting detection triggers chief accountant review regardless of amount | Bypasses lower approver |
| R-010 | System shall remember last threshold re-basing date; re-baseline annually | Notify admin if not re-balanced in 365 days |

## Processes

### P-06: Invoice Approval Workflow Process

1. **Initiation**: User creates invoice → status = DRAFT
2. **Threshold Check**: System evaluates invoice amount against company's threshold matrix
3. **Routing**:
   - amount ≤ T1: Auto-approved (if PO matched) → APPROVED
   - T1 < amount ≤ T2: Route to Manager → wait for approval → APPROVED/REJECTED
   - T2 < amount ≤ T3: Route to Chief Accountant → wait for approval → APPROVED/REJECTED
   - T3 < amount ≤ T4: Route to Director → wait for approval → APPROVED/REJECTED
   - amount > T4: Route to ADMIN/Board → wait for approval → APPROVED/REJECTED
4. **Approval**: Assigned approver reviews and acts (approve/reject)
5. **Audit**: System records audit log entry with full context
6. **Exception Handling**: 
   - Splitting detected → bypasses lower thresholds → chief accountant review
   - Delegation → delegate acts on behalf
   - LAW-type config change blocked → migration required
7. **Completion**: Invoice status = APPROVED → proceeds to payment run

### P-07: Threshold Configuration Management

1. Admin proposes new threshold config via System Settings update
2. System validates: thresholds must be ascending, within reasonable bounds
3. If CONFIG-type flag: 1st approval (accountant) → 2nd approval (chief accountant)
4. If LAW-type flag: raise FlagLockedError, require migration
5. Audit log records: config_version increment, before/after values, actors
6. Cache invalidation: all pending invoices re-evaluated against new thresholds
7. Notify: admin and chief accountant of config change

### P-08: Splitting Detection and Prevention

1. Invoice created → system checks for pattern: same vendor, within 24h, amounts near thresholds
2. If pattern detected → flag SplittingEvent → route to chief accountant
3. Chief accountant reviews → approve/reject with reason
4. If detected → system adds note to invoice: "Splitting detected - total under review"
5. Audit log: splitting_event_id, involved_invoice_ids, total_amount, action_taken

## Templates

### T-001: Approval Request Template

```json
{
  "invoice_id": "uuid",
  "invoice_number": "INV-2026-001",
  "amount": 28500.00,
  "currency": "VND",
  "threshold_band": "T3",
  "required_approver": "CHIEF_ACCOUNTANT",
  "reason": "Invoice amount exceeds $5K manager threshold",
  "submitted_at": "2026-01-15T10:30:00Z",
  "company_id": "uuid"
}
```

### T-002: Approval Matrix Template (CSV)

```
band,max_amount,approver_role,description
T1,500,AUTO,"Auto-approval under $500 with PO match"
T2,5000,MANAGER,"Manager approval $500-$5K"
T3,25000,CHIEF_ACCOUNTANT,"Chief accountant approval $5K-$25K"
T4,100000,DIRECTOR,"Director approval $25K-$100K"
T5,above,ADMIN,"Above $100K requires executive sign-off"
```

### T-003: Delegation of Authority Template

```json
{
  "delegator_id": "uuid",
  "delegate_id": "uuid",
  "effective_from": "2026-01-15",
  "effective_to": "2026-02-15",
  "scope": "all_pending_approvals",
  "reason": "Chief accountant on maternity leave",
  "approved_by": "ADMIN",
  "created_at": "2026-01-15T09:00:00Z"
}
```

### T-004: Splitting Detection Alert Template

```json
{
  "detection_id": "uuid",
  "vendor_tax_id": "123456789011",
  "triggering_invoices": ["INV-001", "INV-002"],
  "individual_amounts": [4800.00, 4700.00],
  "total_amount": 9500.00,
  "threshold_bypassed": "T2 ($5K)",
  "detected_at": "2026-01-15T10:30:00Z",
  "status": "pending_review",
  "reviewed_by": null,
  "company_id": "uuid"
}
```

## Exception Paths

| Scenario | Path |
|----------|------|
| E-001 | Invoice amount exactly at threshold boundary → included in higher band (inclusive lower, exclusive upper, or defined by company config) |
| E-002 | No approver available → system routes to next level up + notifications to all levels |
| E-003 | Company without configured thresholds → use defaults; prompt admin to configure |
| E-004 | LAW-type threshold change attempt → raise FlagLockedError with migration guidance |
| E-005 | Splitting detected but vendor is approved and spend is legitimate → chief accountant overrides with justification, audit log records override |
| E-006 | Invoice cancelled after approval → audit log records cancellation, does not reverse approval |
| E-007 | Delegation expiry → delegate no longer receives notifications, original approver resumes |
| E-008 | Threshold config re-baseline → new thresholds applied; old thresholds archived in audit log |

## Implementation Notes

1. **Existing code integration**: 
   - Extend `Invoice.approve()` to perform threshold check before status change
   - Add threshold check in `SystemSettingsService.update_config()` with 2nd approval enforcement
   - Use existing `@casbin_required` decorator pattern for RBAC

2. **Database changes needed**:
   - New table: `approval_thresholds` (company_id, band, max_amount, approver_role, is_active)
   - New table: `approval_delegations` (delegator_id, delegate_id, effective_from, effective_to, scope, reason)
   - New table: `splitting_events` (detection_id, vendor_tax_id, triggering_invoice_ids, total_amount, status)
   - Extend `invoice` table or add `approval_status` column (already has `status` with APPROVED)

3. **Audit log integration**: Reuse existing `SystemAuditLogModel` (entity_type=invoice, action=approve/threshcheck/splitting)

4. **Vietnamese compliance**: 
   - Thresholds must align with Circular 99/2025 requirements for documented accounting policies
   - E-invoice approval must follow GDT registration requirements
   - MST validation on partner_tax_id still applies

5. **PROD ENV**: Default thresholds operational immediately; configurable via System Settings UI (deferred) or migration patch

## Open Questions (for BA/Client Confirmation)

1. What are the approved dollar thresholds for your company? (Confirm or accept defaults)
2. What is the approval role hierarchy? (Confirm: ACCOUNTANT → CHIEF_ACCOUNTANT → ADMIN → DIRECTOR)
3. Should splitting detection use 24h window or different period?
4. What is the maximum delegation period (default 30 days, propose if different)?
5. Should thresholds be per-company or global defaults with per-company overrides?
6. What is the desired audit retention period before cold storage (default 2y per P-05)?