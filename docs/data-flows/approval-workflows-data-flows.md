# Data Flow Design: Invoice Approval Workflows

## DF-001: Invoice Creation → Threshold Check → Approval Routing

### Data Flow Diagram

```
[Create Invoice] API Request
       │
       ▼
[Invoice Service] - validates inputs, creates Invoice entity
       │
       ├──→ [add_item()] → recalculate subtotal, vat_total, grand_total
       │           │
       │           └──→ Invoice entity stored in DB, status=DRAFT
       │
       └──→ [threshold_check(amount, company_id)]
               │
               ├──→ amount ≤ T1 ($500) → [auto_approve_path]
               │       │
               │       └──→ [PO matched?]
               │               │   │   Yes → Auto-set status=APPROVED
               │               │   No → Route to manager (UC-002 path)
               │               │
               │               └──→ No PO, amount ≤ T1 → Route to manager
               │
               ├──→ T1 < amount ≤ T2 ($500-$5K) → [manager_approval_path]
               │       │
               │       └──→ Route approval request to MANAGER role
               │           │
               │           └──→ [Manager approves via UI]
               │                   │
               │                   └──→ status DRAFT → APPROVED
               │
               ├──→ T2 < amount ≤ T3 ($5K-$25K) → [chief_accountant_path]
               │       │
               │       └──→ Route approval request to CHIEF_ACCOUNTANT role
               │           │
               │           └──→ [Chief Accountant approves]
               │
               ├──→ T3 < amount ≤ T4 ($25K-$100K) → [director_path]
               │       │
               │       └──→ Route approval request to DIRECTOR role
               │
               └──→ amount > T4 (>$100K) → [admin_path]
                       │
                       └──→ Route approval request to ADMIN/BOARD role
```

### Data Elements Passing Through Flow

| Data Element | Source | Destination | Purpose |
|--------------|--------|-------------|---------|
| invoice_id | UI/Creator | Threshold Service | Identify invoice for check |
| invoice_amount | UI/Invoice creation | Threshold Service | Determine which band |
| company_id | User session / context | Threshold Service | Look up company config |
| threshold_band (T1-T5) | Threshold Service | Approval Router | Which approver role |
| approver_role (MANAGER/CA/DIRECTOR/ADMIN) | Threshold Service | RBAC Decorator (@casbin_required) | Authorization check |
| po_matched boolean | Invoice lines / UI | Threshold Service | Auto-approval condition |
| splitting_detection_flag | System algorithm | Splitting Service | Pattern detection |
| delegation_status | Approval Delegations table | Approval Router | Override delegator if applicable |
| audit_context (action, before/after) | System | Audit Log Model | Immutable record |

### Data Flow Sequence (Happy Path - $3,500 invoice)

```
1. User POSTs /invoices with amount=$3,500, vendor=XYZ Corp
2. Backend creates Invoice entity, status=DRAFT, stores in DB
3. Invoice Service calls threshold_check(3500, company_id)
4. Threshold Service evaluates: 3500 ≤ 500? No. 500 < 3500 ≤ 5000? Yes → T2 band
5. Threshold Service returns: {band: "T2", approver: "MANAGER", auto_approve: false}
6. Approval Router sends notification to manager via RBAC-enforced endpoint
7. Manager receives notification, clicks "Approve" in UI
8. @casbin_required('MANAGER') decorator validates manager role
9. Invoice.approve() called → status DRAFT → APPROVED, updated_at=timestamp
10. Audit Log Model created: entity_type="invoice", entity_id=<id>, action="approve", approver="MANAGER", amount=3500, timestamp
11. Invoice now APPROVED → proceeds to payment run
```

### Data Flow Sequence (Auto-Approval - $350 invoice with PO)

```
1. User POSTs /invoices with amount=$350, po_reference="PO-2026-001"
2. Backend creates Invoice entity, status=DRAFT, stores in DB
3. Invoice Service calls threshold_check(350, company_id)
4. Threshold Service evaluates: 350 ≤ 500? Yes → T1 band
5. Threshold Service checks: po_matched = true (PO reference exists and validated)
6. Since T1 AND po_matched: Auto-set status=APPROVED (no human in loop)
7. Invoice.approve() called internally (or status set directly)
8. Audit Log Model created: entity_type="invoice", action="auto_approve", po_matched=true, amount=350, timestamp
9. Invoice immediately APPROVED → proceeds to payment run
```

### Data Flow Sequence (Splitting Detection - $4,800 + $4,700 from same vendor)

```
1. User creates Invoice INV-001, amount=$4,800, vendor_tax_id="123456789011"
   → INV-001 stored, timestamp=t1

2. User (or same vendor) creates Invoice INV-002, amount=$4,700, vendor_tax_id="123456789011"
   → INV-002 stored, timestamp=t2 (within 24h of t1)

3. System Splitting Service runs post-INV-002 creation:
   a. Query: SELECT * FROM invoices WHERE vendor_tax_id='123456789011' AND created_at >= t2-24h
   b. Results: INV-001 ($4,800), INV-002 ($4,700)
   c. Calculate: total = 9,500; individual amounts both < T2 ($5,000)
   d. Pattern match: total > threshold, individual amounts under threshold → SPLITTING DETECTED

4. System creates Splitting Event record:
   - detection_id = uuid
 - vendor_tax_id = "123456789011"
 - triggering_invoice_ids = ["INV-001", "INV-002"]
 - individual_amounts = [4800, 4700]
 - total_amount = 9500
 - threshold_bypassed = "T2 ($5K)"
 - status = "pending_review"
 - detected_at = now

5. Both invoices routed to chief accountant:
   - Approval Router reads: splitting_event.status = "pending_review"
   - Bypasses normal threshold check for both invoices
   - Routes to CHIEF_ACCOUNTANT regardless of individual amounts

6. Chief accountant reviews splitting event:
   - UI shows: "Splitting detected: 2 invoices, vendor XYZ, total $9,500"
   - Chief accountant clicks "Approve with justification"

7. Audit Log entries created:
   - action="splitting_override", approver="CHIEF_ACCOUNTANT", 
     splitting_event_id, involved_invoice_ids, total_amount, justification

8. Both invoices status changed to APPROVED
9. Both invoices proceed to payment (consolidated)
```

### Data Flow Sequence (Delegation - Chief Accountant on Leave)

```
1. Chief accountant sets delegation before leave:
   - effective_from = today (2026-01-15)
   - effective_to = today + 14 days (2026-01-29, within 30-day max)
   - delegate_id = deputy_ca_id (deputy chief accountant)
   - scope = "all_pending_approvals"
   - reason = "On maternity leave"
   - stored in approval_delegations table

2. During delegation period, pending approvals flow:
   - System checks: approval_delegations table for current user
   - If chief_accountant has pending approvals AND delegation active:
     - System: "show notifications to delegate instead"
     - delegate receives all chief accountant's pending approval alerts
   
3. Deputy chief accountant acts:
   - Deputy logs in → sees "5 pending approvals (on behalf of CA)"
   - Deputy clicks "Approve" on invoice
   - @casbin_required('CHIEF_ACCOUNTANT') but delegation flag present
   - System: "approve on behalf of delegator, record in audit"

4. Audit Log entries:
   - action="approve", approver="DELEGATE (on behalf of CHIEF_ACCOUNTANT)"
   - invoice_id, amount, timestamp
   - delegation_id referenced

5. After delegation expires (2026-01-29):
   - System: "delegation expired, returning approvals to original approver"
   - Any remaining approvals revert to chief accountant
   - Notifications: "Chief accountant approvals resumed"
```

### Data Flow Sequence (Threshold Configuration Update)

```
1. Admin proposes new thresholds via System Settings UI:
   - T1: $200 (was $500)
   - T2: $3,000 (was $5,000)
   - T3: $15,000 (was $25,000)
   - T4: $50,000 (was $100,000)
   - submitted_at = now

2. System validates:
   - ascending order: 200 < 3000 < 15000 < 50000 ✓
   - within reasonable bounds (max $1M, min $1)
   - company_id lookup from context

3. Since CONFIG-type flag: 1st approval path initiated:
   - SystemSettingsService.update_config() called
   - config_version incremented: from 3 → 4
   - before_values captured: {T1:500, T2:5000, T3:25000, T4:100000}
   - after_values captured: {T1:200, T2:3000, T3:15000, T4:50000}
   - actor=ADMIN, action="config_propose"
   - Audit Log: entity_type="system_config", action="update_proposed", before/after, config_version=4

4. Chief accountant notified of pending 2nd approval:
   - Email/HTMX notification: "Threshold config update pending CA approval"
   - Chief accountant reviews proposed changes

5. Chief accountant approves 2nd:
   - SystemSettingsService.update_config() called again with actor=CHIEF_ACCOUNTANT
   - 2nd approval check: validates CA role has authority
   - config_version incremented: 4 → 5
   - New thresholds saved to DB
   - Cache invalidation: all pending invoices re-evaluated
   - Old thresholds archived in audit log (config_version history)

6. Audit Log final entry:
   - entity_type="system_config", action="update_completed"
   - before_values (pre-2nd-approval draft), after_values (active new thresholds)
   - actors: ADMIN (submitted), CHIEF_ACCOUNTANT (approved)
   - config_version=5

7. System behavior after update:
   - All new invoices use new thresholds immediately
   - Pending invoices (in DRAFT) re-evaluated against new thresholds
   - Already-approved invoices: no retroactive change (audit integrity)
   - Admin and stakeholders notified: "Thresholds updated effective 2026-01-15"
```

### Database Schema Changes (Required)

#### New Table: approval_thresholds

```sql
-- Threshold matrix per company
CREATE TABLE approval_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    band VARCHAR(10) NOT NULL,  -- T1, T2, T3, T4, T5
    max_amount DECIMAL(14,2) NOT NULL,  -- e.g., 500.00, 5000.00
    approver_role VARCHAR(50) NOT NULL,  -- MANAGER, CHIEF_ACCOUNTANT, DIRECTOR, ADMIN
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(company_id, band)
);
```

#### New Table: approval_delegations

```sql
-- Delegation of authority records
CREATE TABLE approval_delegations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delegator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delegate_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    effective_from DATE NOT NULL,
    effective_to DATE NOT NULL,
    scope VARCHAR(20) NOT NULL,  -- "all_pending", "band_T1_T2", etc.
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(delegator_id, effective_from, effective_to)
);
```

#### New Table: splitting_events

```sql
-- Invoice splitting detection events
CREATE TABLE splitting_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_tax_id VARCHAR(20) NOT NULL,
    triggering_invoice_ids UUID[] NOT NULL,  -- ARRAY of invoice IDs
    individual_amounts DECIMAL(14,2)[] NOT NULL,
    total_amount DECIMAL(14,2) NOT NULL,
    threshold_bypassed VARCHAR(20) NOT NULL,  -- e.g., "T2 ($5K)"
    status VARCHAR(30) DEFAULT 'pending_review',  -- pending_review, approved, rejected
    detected_at TIMESTAMP DEFAULT now(),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    justification TEXT,
    company_id UUID NOT NULL REFERENCES companies(id)
);
```

#### Extended: invoice table (if needed)

The existing `invoices` table already has `status` column with values including `APPROVED`. No new column needed - the `status` field handles the approval workflow state.

### Data Flow API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `POST /invoices` | Create invoice | Creates invoice in DRAFT, triggers threshold check | `@casbin_required` (per role) |
| `POST /invoices/{id}/approve` | Approve invoice | Performs approval with threshold/RBAC check | `@casbin_required('MANAGER'/'CHIEF_ACCOUNTANT'/'DIRECTOR'/'ADMIN')` |
| `GET /system-settings/thresholds` | Get current thresholds | Returns company's threshold matrix | Admin |
| `PUT /system-settings/thresholds` | Update thresholds | Proposes new threshold config | Admin + 2nd approval (CA) |
| `POST /approval/delegations` | Set delegation | Records delegation of authority | Chief Accountant |
| `GET /approval/splitting-events` | Get splitting events | Returns detected splitting patterns | Auditor/Admin |

### Integration with Existing Code

1. **Invoice.approve()** (src/domain/entities/invoice.py:117-121):
   - Currently: checks status ≠ DRAFT → ValueError, then status = APPROVED
   - Enhanced: add threshold check before status change
   - If amount under T1 with PO → auto-approved
   - If amount in T2-T5 → route to appropriate approver via RBAC
   - If splitting detected → route to chief accountant

2. **SystemSettingsService.update_config()** (src/application/services/system_settings_service.py):
   - Currently: performs setattr directly, no LAW/2nd approval check
   - Enhanced: add CONFIG-type 2nd approval enforcement
   - Add LAW-type FlagLockedError for threshold changes
   - Increment config_version, emit audit events

3. **@casbin_required decorator** (existing RBAC):
   - Already on 8 API routes
   - Enhanced: add threshold band checking within decorator or wrapper
   - Role hierarchy: ACCOUNTANT → CHIEF_ACCOUNTANT → ADMIN → DIRECTOR maintained

4. **Audit logging** (SystemAuditLogModel):
   - Already exists in models.py
   - Enhanced: add new action types: "auto_approve", "splitting_override", "threshold_config_update"
   - Ensure append-only (no DELETE, archive after 2y per P-05)

### VIETNAMESE COMPLIANCE NOTES

1. **Circular 99/2025/TT-BTC**: Requires documented accounting policies including approval workflows
2. **MST Validation**: Partner tax_id (`TaxId` value object: `^\d{10}$` or `^\d{10}-\d{3}$`) still applies
3. **E-Invoice Integration**: Invoice approval must precede e-invoice issuance (separate module)
4. **Audit Retention**: Appendix IA of Decree 70/2025 - append-only logs, cold storage after 2 years
5. **Threshold Config**: LAW-type flags (if any threshold params declared LAW) require migration; CONFIG-type requires 2nd approval pattern already established

### PROD ENV STATUS

- **Default thresholds operational immediately**: T1=$500, T2=$5K, T3=$25K, T4=$100K, T5=above
- **Configurable via System Settings**: Admin can propose changes (requires 2nd CA approval for CONFIG-type)
- **No PROD deployment breakage**: Uses existing DB, reuses existing audit log, RBAC decorators
- **Migration path**: IfLAW-type threshold changes needed later, follow existing migration patch pattern

### BACKWARD COMPATIBILITY

- Existing invoices: status field unchanged, approval workflow applies only to new DRAFT invoices
- Existing API routes: `@casbin_required` decorators unchanged, enhanced with threshold checking internally
- Existing tests: 92 passing tests unchanged; 2 pre-existing failures (Python 3.13 UUID), 14 pre-existing errors (SQLAlchemy session) unaffected
- New functionality opt-in: companies can use defaults or configure; no forced upgrade

### OPEN QUESTIONS FOR BA/CLIENT

1. Confirm default thresholds: T1=$500, T2=$5K, T3=$25K, T4=$100K, T5=above (or propose alternatives)
2. Confirm approval role hierarchy: ACCOUNTANT → CHIEF_ACCOUNTANT → ADMIN → DIRECTOR (or adjust)
3. Confirm splitting detection window: 24h (or propose different: 48h, 72h, custom per company)
4. Confirm max delegation period: 30 days (or propose: 14 days, 45 days, custom)
5. Confirm audit retention before cold storage: 2y per existing policy P-05 (or different)
6. Should thresholds be per-company or global defaults with overrides?
7. Any Vietnamese-specific threshold considerations (tax regimes, sector-specific rules)?