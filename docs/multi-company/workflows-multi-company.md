# Workflows — Multi-Company / Master-Module
> v0.1 | Status: DRAFT | Derives from: docs/brd-multi-company.md

---

## W-001: Subsidiary Onboarding Workflow

```
Trigger: CFO creates new legal entity in group
─────────────────────────────────────────────
[Start]
  → Create Company record (UC-0001)
    ├─ Validate MST (^\d{10}(-\d{3})?$)
    ├─ Select Accounting Regime (SME/Enterprise)
    ├─ Select COA template (Circular 99/2025)
    └─ Assign fiscal year
  → Assign Users (UC-0002)
    ├─ Bookkeeper (entity-level CRUD)
    └─ Manager (entity-level approval)
  → Configure e-invoice series per MST
  → Register with Tổng cục Thuế for this MST (UC-0012)
  → [End: Ready for posting]
```

### Swimlanes (simplified)

| Step | System | CFO / SysAdmin | Tax Admin |
|---|---|---|---|
| Create company | Records creation | Fills form | — |
| Validate MST | Checks format + uniqueness | — | Confirms with Tổng cục Thuế |
| Assign users | Stores role mapping | Selects users | — |
| Register software | — | Submits form | Validates registration |

---

## W-002: Subsidiary Period-End Close

```
Trigger: Month-end / quarter-end / year-end for subsidiary
─────────────────────────────────────────────
[Start: Subsidiary Bookkeeper initiates close]
  → Halt new postings (except closing entries)
  → Run trial balance check (system)
    ├─ All vouchers balanced? → Yes → Continue
    └─ No → Flag unbalanced Voucher IDs → [Block]
  → Authorized user (Manager) confirms close
  → System creates PeriodLock record
  → System publishes "PeriodClosed" event
  → System notifies Group CFO via in-app notification
  → [End: Subsidiary locked]
```

### Parallel path (if unbalanced):
```
→ Unbalanced voucher alert
→ Bookkeeper investigates
→ Manager approves correcting entry
→ Re-run check
→ Close
```

---

## W-003: Consolidated BCTC Generation

```
Trigger: All subsidiaries closed; CFO initiates consolidation
─────────────────────────────────────────────
[Start: Consolidation Group has ≥2 locked subsidiaries]
  → Validate all subsidiaries locked for target period
    ├─ All locked → Continue
    └─ Any open → ["Close all subsidiaries first"] → [Halt]
  → Create ConsolidationRun (status=DRAFT)
  → Pull Trial Balance snapshot from each subsidiary
    └─ Snapshot immutable once pulled
  → ConsolidationService.calculate_trial_balance()
    → Combined trial balance presented to CFO
  → CFO adds master adjusting entries (UC-0010)
    ├─ NST elimination (e.g., intercompany receivables/payables)
    └─ NLD elimination (e.g., unrealized profit, depreciation)
  → CFO clicks [Generate Consolidated BCTC]
  → System produces:
    ├─ BCTC TSCĐ hợp nhất (Bảng cân đối kế toán)
    ├─ BCTC KQKD hợp nhất (Kết quả hoạt động kinh doanh)
    ├─ BCTC LCTT hợp nhất (Lưu chuyển tiền tệ — direct method)
    └─ Thuyết minh hợp nhất (Notes per Circular 99/2025 Mẫu 07/BCTC)
  → CFO reviews output
  → CFO approves → run status=POSTED, period=LOCKED
  → System: export to PDF / Excel (Circular 99 templates)
  → System: archive run (immutable)
  → [End: Consolidated BCTC ready for statutory filing]
```

### Exception branches:
- **Imbalance in elimination entries** → Block approval; CFO corrects
- **Subsidiary TB changed post-snapshot** → Warning: "Subsidiary B modified after snapshot. Refresh?"
- **Run already exists for period+group** → "Consolidation for 2025 already exists"; suggest reopening

---

## W-004: Intercompany Invoice Flow

```
Trigger: Subsidiary A sells goods/services to Subsidiary B
─────────────────────────────────────────────
[Subsidiary A Bookkeeper]
  → Creates invoice to customer = Subsidiary B
  → System detects MST of counterparty matches internal company registry
  → System sets is_intercompany=True; stores counterpart company_id
  → Invoice posted (A's AR / B's AP booked automatically by system or by B)
  → [Invoice flagged]

[System background / next Subsidiary B bookkeeping session]
  → B's bookkeeper sees matching AP entry
  → B confirms receipt of goods/services
  → [Both sides matched]

[Consolidation run]
  → System surfaces intercompany invoice pairs for period
  → CFO vetting
  → CFO adds NST eliminating entry (if not already matched)
  → Run approves
```

### Rules:
- Intercompany invoice must use same currency as parent group reporting currency (v1: VND only)
- Cannot create intercompany between company and itself
- Netting allowed: AR/AP can be netted per Circular standards

---

## W-005: User Provisioning & Access Management

```
Trigger: New employee joins group; or user role changes
─────────────────────────────────────────────
[Start: SysAdmin or GROUP_CFO]
  → Create User account (if new)
  → Assign to Company(ies)
    ├─ Assign 1 company → SUBSIDIARY_BOOKKEEPER
    ├─ Assign all subsidiaries → GROUP_CFO (for CFO account)
    └─ Assign group read-only → AUDITOR
  → User logs in
  → System shows company switcher
  → User selects company
  → All subsequent API calls include company_id filter automatically
  → [End: Access scoped]
```

### Rules:
- MASTER_ADMIN always has access to all companies
- SUBSIDIARY_BOOKKEEPER cannot be assigned to 0 companies (error on login)
- Removing user's last company assignment deactivates access

---

## W-006: Deactivate Subsidiary & Archive

```
Trigger: Legal entity liquidated, merged, or sold
─────────────────────────────────────────────
[Start]
  → Close all open periods (W-002)
  → Submit all pending tax declarations (L1-L5 compliance)
  → Group CFO initiates deactivation (UC-0008)
  → System: sets status=INACTIVE, is_active=False
  → System: blocks new postings to company
  → System: maintains read-only access to historical data
  → System: archives company's data in compliance with Luật Lưu trữ
  → Optional: data export for handover to buyer / auditor
  → [End: Archived; read-only]
```

### Exception:
- **Pending audit** → Cannot archive until audit complete

---

## W-007: COA Regime Change (SME → Enterprise)

*(Rare; typically triggered by business growth)*

```
Trigger: Subsidiary grows out of SME regime into Enterprise regime
─────────────────────────────────────────────
[Start: CFO requests regime change]
  → System validates: cannot change if open periods
  → System validates: Circular 99/2025 Enterprise COA complexity
  → System proposes COA migration path
    ├─ New accounts to add
    ├─ Accounts to merge/reclassify
    └─ Periods affected
  → CFO approves migration plan
  → System: closes current periods first
  → System: creates new COA structure (copy + modify)
  → System: reclassifies previous period balances per new COA (if approved)
  → Regime updated; FY continues
  → [End: New COA active]
```

--- END OF FILE ---
