# Templates: Approval Workflows / Thresholds

## T-001: Approval Request Template (JSON)

Used when system routes invoice for approver notification. Includes all context needed for approver decision.

```json
{
  "invoice_id": "c2f3d4e5-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
  "invoice_number": "INV-2026-015",
  "amount": 28500.00,
  "currency": "VND",
  "threshold_band": "T3",
  "max_amount_band": 25000.00,
  "required_approver_role": "CHIEF_ACCOUNTANT",
  "approver_name": "Nguyen Van A - Chief Accountant",
  "reason": "Invoice amount exceeds $5K manager threshold, requires chief accountant sign-off",
  "vendor_name": "Công ty TNHH Đầu tư X",
  "vendor_tax_id": "123456789011",
  "invoice_date": "2026-01-10",
  "due_date": "2026-02-09",
  "status": "DRAFT",
  "items_count": 4,
  "subtotal": 25000.00,
  "vat_total": 3500.00,
  "grand_total": 28500.00,
  "currency": "VND",
  "submitted_at": "2026-01-15T10:30:00Z",
  "company_id": "a1b2c3d4-e5f6-7a89-b0c1-d2e3f4a5b6c7",
  "po_reference": "PO-2026-015",
  "splitting_detection": false,
  "delegation_active": false
}
```

---

## T-002: Approval Matrix Template (CSV)

Used for initial config setup or re-balancing. Maps dollar bands to approver roles.

```
band,max_amount,approver_role,description,TVApplicable
T1,500.00,AUTO,"Auto-approval under $500 with PO match",YES
T2,5000.00,MANAGER,"Manager approval $500-$5,000",YES
T3,25000.00,CHIEF_ACCOUNTANT,"Chief accountant approval $5K-$25K",YES
T4,100000.00,DIRECTOR,"Director approval $25K-$100K",YES
T5,above,ADMIN,"Above $100K requires executive sign-off",YES
```

**Usage:**
- Import CSV into system Settings → Thresholds page
- Validates: bands must be in ascending order (T1 < T2 < T3 < T4 < T5)
- Each band max_amount must be > previous band's max_amount
- `AUTO` band auto-approves if PO matched, otherwise routes to next level

---

## T-003: Delegation of Authority Template (JSON)

Used when approver designates stand-in during absence.

```json
{
  "delegation_id": "d4e5f6a7-8b9c-0d1e-2f3a-4b5c6d7e8f9a",
  "delegator_id": "c2f3d4e5-6a7b-8c9d-0e1f-2a3b4c5d6e7f",  -- chief_accountant UUID
  "delegate_id": "f3a4b5c6-7d8e-9f0a-1b2c-3d4e5f6a7b8c",  -- deputy chief_accountant UUID
  "effective_from": "2026-01-15",
  "effective_to": "2026-02-14",
  "scope": "all_pending_approvals",
  "reason": "Chief accountant on maternity leave",
  "approved_by": "ADMIN_JOHNSON",  -- ADMIN who validated the delegation
  "created_at": "2026-01-15T09:00:00Z",
  "status": "active",
  "notes": "Delegate can approve/reject invoices up to $100K threshold. Extend before 2026-02-14 if leave prolonged."
}
```

**Validations:**
- `effective_to - effective_from` ≤ 30 days (system rejects if longer)
- delegator_id must have CHIEF_ACCOUNTANT role
- delegate_id must have CHIEF_ACCOUNTANT or ADMIN role
- Only one active delegation per delegator at a time
- If scope includes specific bands, format: "band_T1_T2" or "band_T3_T4"

---

## T-004: Splitting Detection Alert Template (JSON)

Generated when system detects invoice splitting pattern.

```json
{
  "detection_id": "a5b6c7d8-9e0f-1a2b-3c4d-5e6f7a8b9c0d",
  "vendor_tax_id": "123456789011",
  "vendor_name": "Công ty TNHH bán buôn X",
  "triggering_invoices": ["INV-2026-001", "INV-2026-002"],
  "individual_amounts": [4800.00, 4700.00],
  "total_amount": 9500.00,
  "threshold_bypassed": "T2 ($5,000)",
  "detected_at": "2026-01-15T10:30:00Z",
  "status": "pending_review",
  "reviewed_by": null,
  "reviewed_at": null,
  "company_id": "a1b2c3d4-e5f6-7a89-b0c1-d2e3f4a5b6c7",
  "company_name": "Công ty ABC Ltd",
  "splitting_pattern_analysis": {
    "invoices_within_24h": true,
    "individual_under_threshold": true,
    "total_exceeds_threshold": true,
    "pattern_confidence": "HIGH"
  },
  "action_required": "Chief accountant review and approval with justification"
}
```

**Pattern Conditions (automatically checked by system):**
- ≥2 invoices from same vendor_tax_id within 24h window
- Each individual amount under the next threshold band (T2 $5K in this case)
- Combined total exceeds that threshold band
- No prior splitting events for this vendor in last 30 days (or counted for pattern learning)

---

## T-005: Threshold Configuration Change Proposal Template (JSON)

Used when admin proposes new threshold matrix.

```json
{
  "proposal_id": "e1f2d3c4-b5a6-9f8e-7d_cba9-87654_3210",
  "company_id": "a1b2c3d4-e5f6-7a89-b0c1-d2e3f4a5b6c7",
  "old_thresholds": {
    "T1": 500.00,
    "T2": 5000.00,
    "T3": 25000.00,
    "T4": 100000.00
  },
  "new_thresholds": {
    "T1": 200.00,
    "T2": 3000.00,
    "T3": 15000.00,
    "T4": 50000.00
  },
  "proposed_by": "ADMIN_JOHNSON",
  "proposed_at": "2026-01-15T14:30:00Z",
  "reason": "Annual re-basing: invoice distribution shifted, new T2 handles 65% of invoices vs previous 55%",
  "config_version_before": 3,
  "config_version_after_proposal": 4,
  "requires_2nd_approval": true,
  "2nd_approver_role": "CHIEF_ACCOUNTANT",
  "2nd_approval_deadline": "2026-01-22T14:30:00Z",  // 7 days from proposal
  "status": "pending_2nd_approval",
  "audit trail": {
    "before_values_captured": true,
    "after_values_captured": false,  -- set after 2nd approval
    "config_version_incremented": true  -- 3 → 4 at proposal, 4 → 5 after 2nd
  }
}
```

**Workflow:**
1. Admin submits proposal → status = `pending_2nd_approval`, config_version incremented
2. Chief accountant reviews → approves or rejects
3. If approved: config_version incremented again, new thresholds active, cache invalidated
4. If rejected: config_version reverts, admin must resubmit

---

## T-006: Annual Re-Basing Report Template (Markdown)

Document of threshold re-basing decision at fiscal year start.

```markdown
# Threshold Re-Basing Report

**Company:** Công ty ABC Ltd  
**Report Date:** 2026-01-15  
**Fiscal Year:** 2025 (or Calendar Year 2026)  
**Prepared By:** Admin Johnson  

## Executive Summary

Analysis of 12 months (2025-01-01 to 2025-12-31) invoice distribution against current threshold matrix.

## Invoice Distribution by Threshold Band

| Band | Max Amount | Invoice Count | % of Total Invoice Count | % of Total Dollar Amount |
|------|-----------|---------------|-------------------------|-------------------------|
| T1   | $500      | 128           | 12%                     | 3%                      |
| T2   | $5,000    | 412           | 39%                     | 12%                     |
| T3   | $25,000   | 315           | 30%                     | 35%                     |
| T4   | $100,000  | 187           | 18%                     | 48%                     |
| T5   | Above     | 12            | 1%                      | 2%                      |
| **Total** | **--** | **1,054** | **100%** | **100%** |

## Analysis

- T2 ($5K) handles 39% of invoice count but only 12% of dollar amount → efficient
- T4 ($100K) handles 18% of count but 48% of dollar amount → executive attention needed
- 3 vendors detected with splitting patterns (total $28,500 attempted bypass)
- No significant business model changes in 2025

## Proposed New Thresholds

| Band | Old Max | New Max | Rationale |
|------|---------|---------|-----------|
| T1   | $500    | $300    | Better match low-value transaction volume |
| T2   | $5,000  | $4,000  | Align with new vendor payment terms |
| T3   | $25,000 | $20,000 | Reflect current high-value invoice pattern |
| T4   | $100,000| $75,000 | More frequent director review for mid-range spend |

## Approval

- **Proposed By:** Admin Johnson
- **2nd Approval (Chief Accountant):** Nguyen Van A - APPROVED on 2026-01-15
- **Config Version:** 3 → 4

## Effectiveness Metrics (Post-Implementation, 90 days)

- Invoice auto-approval rate: Target X%, Actual Y%
- Average approval cycle time: Target < 24h, Actual Z h
- Splitting events detected: Target < 5/month, Actual W/month
- Stakeholder satisfaction: Survey results

## Next Review

- **Date:** 2027-01-15 (annual)
- **Trigger:** Any time business model changes >20% in invoice patterns
```

---

## T-007: Audit Log Entry Template (JSON)

Append-only record for all approval workflow actions.

```json
{
  "log_id": "f6e5d4c3-b2a1-0f9e-8d7c-6b5a4_3c2d1e0f",
  "entity_type": "invoice",
  "entity_id": "c2f3d4e5-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
  "entity_number": "INV-2026-015",
  "action": "approve",  -- auto_approve, approve, reject, splitting_override, threshold_config_update, re_basing
  "actor": "MANAGER_NguyenVanA",  -- role + name, or "SYSTEM", or "ADMIN_JOHNSON"
  "actor_id": "u1v2w3x4-y5z6-7a8b-9c0d-e1f2a3b4c5d6",
  "timestamp": "2026-01-15T10:35:00Z",
  "previous_status": "DRAFT",
  "new_status": "APPROVED",
  "action_details": {
    "invoice_amount": 28500.00,
    "threshold_band": "T3",
    "approver_role": "CHIEF_ACCOUNTANT",
    "splitting_override": false,
    "delegation_id": null,
    "po_matched": true
  },
  "checksum": "sha256:abc123def456...",  -- for integrity verification
  "archive_status": "active",  -- "active", "archived", "cold_storage"
  "retention_policy": "2y_per_P-05",  -- per process P-05 audit trail guarantee
  "company_id": "a1b2c3d4-e5f6-7a89-b0c1-d2e3f4a5b6c7"
}
```

**Immutable guarantees:**
- `INSERT` only - no `UPDATE` or `DELETE` possible at DB level (triggers prevent modification)
- `checksum` computed at creation, verified on any access
- `retention_policy` enforced via app logic (archive after 2y, cold storage after 5y)
- `entity_type` + `entity_id` composite index for fast querying

**Action types documented:**
- `auto_approve`: Invoice auto-approved (T1 with PO)
- `approve`: Standard approver sign-off (T2-T5)
- `reject`: Approver rejected invoice
- `splitting_override`: Chief accountant overrides splitting detection
- `threshold_config_update`: Config change proposal/completion
- `re_basing`: Annual threshold re-basing decision
- `system_init`: Initial config setup (LAW-type migration)

---

## T-008: Compliance Report Template (Markdown)

For internal auditor quarterly review.

```markdown
# Invoice Approval Compliance Report

**Period:** Q1 2026 (2026-01-01 to 2026-03-31)  
**Company:** Công ty ABC Ltd  
**Auditor:** Internal Audit Team  
**Report Date:** 2026-04-10  

## Overview

- Total invoices processed: 1,247
- Auto-approved (T1 with PO): 142 (11.4%)
- Manager-approved (T2): 487 (39.1%)
- Chief Accountant-approved (T3): 312 (25.0%)
- Director-approved (T4): 189 (15.2%)
- Admin/Board-approved (T5+): 19 (1.5%)
- Rejected: 102 (8.2%)
- Splitting events detected: 5

## threshold Compliance

- All invoices above T1 had threshold check performed: ✓ PASS
- No invoices bypassed approval without threshold evaluation: ✓ PASS
- LAW-type flag changes without migration: 0 (zero incidents) ✓ PASS
- CONFIG-type changes with 2nd approval: 4 updates in quarter, all with proper 2nd approval ✓ PASS

## Exception Analysis

### Splitting Events (5 in quarter)

| Detection ID | Vendor | Invoices | Individual Total | Action Taken |
|-------------|--------|----------|-----------------|--------------|
| DEC-001 | Vendor X | INV-001, INV-002 | $9,500 | Chief accountant override, approved with justification |
| DEC-002 | Vendor Y | INV-003, INV-004 | $8,200 | Rejected, pattern noted for future |
| DEC-003 | Vendor Z | INV-005 alone | $4,800 | No splitting (single invoice, normal) |
| DEC-004 | Vendor X (again) | INV-006, INV-007 | $10,100 | Re-escalated, chief accountant reviewed |
| DEC-005 | Vendor W | INV-008 alone | $3,500 | No splitting (under T1, auto-approved) |

**Finding:** Vendor X shows repeated splitting attempts (2 events in quarter). Recommend: vendor payment term review, consolidate orders.

### Delegation Events (3 in quarter)

| Delegation ID | Delegator | Delegate | Duration | Invoices Approved |
|--------------|-----------|----------|----------|-------------------|
| DEL-001 | CA (on leave) | Deputy CA | 14 days | 8 invoices |
| DEL-002 | CA (travel) | Senior Accountant | 7 days | 3 invoices |
| DEL-003 | CA (illness) | Interim CA | 21 days | 12 invoices |

### Self-Approval Block Attempts (4 in quarter)

All blocked by system design, no successful self-approvals. ✓ PASS

## Recommendations

1. Increase T2 threshold from $5,000 to $5,500 to reduce manager workload (15% time savings estimated)
2. Implement vendor consolidation policy to reduce splitting patterns
3. Continue current delegation protocol - functioning well within 30-day max
4. Maintain current audit retention policy (2y active, 5y cold storage)

## Action Items

| ID | Recommendation | Owner | Due Date | Status |
|----|---------------|-------|----------|--------|
| AI-01 | Review vendor X payment terms | Procurement | 2026-05-01 | Open |
| AI-02 | Consider T2 increase to $5,500 | Admin | 2026-06-01 | Planned |
| AI-03 | Vendor splitting pattern monitoring | Internal Audit | Ongoing | Active |

## Summary

**Compliance Status:** COMPLIANT  
**Findings:** 0 critical, 3 minor (all recommendations above)  
**Next Review:** Q2 2026 (2026-04-01 to 2026-06-30)