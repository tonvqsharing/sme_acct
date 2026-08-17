# User Journeys: System Settings Module

---

## Journey 01: New Company Onboarding (CA Perspective)

**Persona:** Kế toán trưởng (Chief Accountant), mid-level, 5-10 years exp
**Goal:** Set up a newly registered Vietnamese SME in the accounting system — complete within 1 business day

```
DAY 1 — MORNING
  Login: admin account (MFA)
  ↓
  Navigate: Settings → Company Setup Wizard
  ↓
  Step 1 — Company Legal Info
    Name: "Công ty TNHH ABC"
    MST: "0123456789"  ← System validates format (L-01)
    Address: "123 Nguyễn Văn Linh, Q.7, TP.HCM"
    Legal rep: "Nguyễn Văn A"
    Company type: "Limited Liability Company"
    Tax authority registration: "Chi cục Thuế Q.7"
    ↓ [Next: validation pass]
  
  Step 2 — Accounting Regime
    Revenue: VND 800M/year (employee count: 8)
    System suggests: TT200 (standard enterprise)
    (would be TT58_MICRO if ≤ VND 3B AND ≤10 employees)
    [CA confirms TT200 — note: once set, changes require filing accounting policy change]
    ↓
  Step 3 — Chart of Accounts
    System loads: TT 200/2014/TT-BTC default COA (111-899)
    CA reviews; selects 4-digit sub-account depth (C-11)
    ↓
  Step 4 — Fiscal Year
    System defaults: Jan 1 – Dec 31
    CA overrides: Apr 1 – Mar 31 (legacy enterprise)
    ↓
  Step 5 — Tax Configuration
    VAT registered: YES
    VAT method: KHẤU TRỪ (DEDUCTION)
    Settlement cycle: MONTHLY
    Input VAT credit rate: 100% (standard)
    ↓
  Step 6 — E-Invoice Mode
    CA selects: CA_SIGNED (GDT-approved PKI)
    System prompts: upload CA cert (or enter CA_signer DN)
    System validates: cert in GDT CA list (c2qz.gdt.gov.vn)
    CA selects primary series: "AA/2026" (already declared to GDT)
    ↓
  Step 7 — Review All
    [CA reviews 15 mandatory + optional settings]
    System highlights items needing accountant sign-off:
      - accounting_regime: regime=TỰ_CHỦ (enterprise) — requires legal review
      - vat_method: khấu trừ — requires legal review
    CA signs: "LEGAL REVIEW STAMP"
    System: legal_reviewed_at = now; legal_reviewed_by = CA user ID
    Config version: 1
    PRODUCTION_READY: TRUE
    ↓
DAY 1 — AFTERNOON (Smoke Test)
  CA runs 3-entry guide:
    1. Customer "Khách hàng X" (MST validated)
    2. Invoice "AA/2026-00001" (valid VAT rate, valid period)
    3. Voucher "PC01" (account codes validated, balanced)
  All pass → CA confirms "Ready for team"
  
DAY 2 — Team Onboarding
  CA adds SA accounts with role-based access
  CA reviews SoD matrix (CREATOR/APPROVER/POSTER roles)
  CA completes USER_ACCESS_REVIEW -> stamped
```

**Journey metrics:**
- Duration target: 4-6 hours total
- Blockers: MST invalidate at GDT, wrong regime choice requiring re-setup
- Success indicator: 3-entry smoke test passes; legal review stamped

---

## Journey 02: Monthly Period Close (CA Perspective)

**Persona:** Kế toán trưởng
**Goal:** Lock accounting period at month-end to prevent backdating

```
Last Business Day of Month
  CA navigates: Settings → Period Management
  ↓
  System shows:
    Jan 2026: LOCKED (locked by CA on Feb 3)
    Feb 2026: LOCKED (locked by CA on Mar 3)
    Mar 2026: OPEN  ← CA focuses here
    Apr 2026: OPEN  ← future, cannot be locked
  ↓
  Pre-flight checks (System runs):
    ☐ JEs in DRAFT: 0
    ☐ Bank reconciliation: balanced
    ☐ Inventory count: posted
    ☐ Tax provision: calculated
    ☐ Mismatch tolerance: < 0.01 VND
  All checks: GREEN
  ↓
  CA selects: "Lock March 2026"
  System: checks CA role (ACCOUNTANT+) ✓
  System: derives period from fiscal_year_start (if Apr FY: Mar = period 12)
  System: creates PeriodLock(lock_type=PERIOD, locked_by=CA)
  System: emits PERIOD_LOCKED audit event
  ↓
  SA (next day) tries to enter 2026-03-28 invoice
  System rejects: "Kỳ kế toán tháng 3/2026 đã KHÓA. Không được nhập liệu ngày hôm trước."
  SA creates invoice with 2026-04-05 → SUCCESS
```

**Emotional beats:** Peace of mind after locking; clear error for SA who forgot the period ended; no data loss.

---

## Journey 03: VAT Quarterly Filing (CA Perspective)

**Persona:** Kế toán trưởng
**Goal:** Generate quarter VAT declaration from system data

```
Quarter End (Mar/Jun/Sep/Dec)
  CA navigates: Tax → VAT Summary
  ↓
  System reads: vat_settlement_cycle = MONTHLY (or QUARTERLY if opted)
  System derives: filing period from accounting_period
  ↓
  System shows pre-populated form:
    - Output VAT: VND 50M (sum of sales invoices)
    - Input VAT: VND 25M (sum of purchase invoices)
    - VAT payable: VND 25M
    - Period: Q1/2026
  ↓
  CA reviews; notes: VAT on purchase from party "XYZ" excluded due to missing MST
  CA adds manual adjustment: + VND 500K (non-deductible portion)
  System records: manual_adjustment_note in audit trail
  ↓
  CA: Export VAT Summary to XML (per tax authority schema)
  ↓
  CA: Uploads via thuedientu.gdt.gov.vn
  ↓
  CA: Marks period "Tax filed" via System flag (audit trail)
  System: records TAX_FILED event
```

**Success indicator:** Tax filing without manual data reconciliation; system matches filed amounts to DB with ≥95% accuracy.

---

## Journey 04: Setting Update by Admin (A Perspective)

**Persona:** Giám đốc (Admin)
**Goal:** Enable cost center requirement mid-year

```
Admin receives request from CA:
  "We need cost centers required starting Q3 for better cost tracking"
  ↓
  A navigates: Settings → Config Flags
  A filters: "cost_center_required"
  System shows: Current value = False (CONFIG flag); requires_2nd_approval = False
  ↓
  A: PATCH /config/flags/cost_center_required
      Body: { "value": true, reason: "Enable cost center tracking in H2" }
      X-Config-Version: 3
  ↓
  System:
    - Records before: false, after: true in config_changes
    - Emits CONFIG_UPDATED audit event
    - Increments config_version to 4
    - Cache invalidated
  ↓
  [No 2nd approval needed]
  ↓
  System takes effect: all NEW vouchers must have at least 1 line with cost_center set
  System publishes: "cost_center_required changed to TRUE on 2026-07-01"
  ↓
  [CA] next day attempts voucher without cost_center:
    "Lỗi: Mục chi phí trống. Vui lòng chọn bộ phận chi phí."
  CA embraces: ok, flag is active
```

---

## Journey 05: Annual Legal Review (CA Perspective)

**Persona:** Kế toán trưởng
**Goal:** Annual legal sign-off; identify any config drift from approved regime

```
Start of Q2 (April)
  System generates: Annual Legal Review Packet
  Contains:
    - Current flag snapshot (JSON)
    - All config_changes since last legal_review stamp
    - Compliance checklist:
        □ fiscal_year matches company charter
        □ vat_method matches tax registration with GDT
        □ retention_years ≥ 10 per LKT 2015
        □ e_invoice_mode matches GDT registration
        □ COA version matches declared accounting regime
        □ All LAW-flagged values match current Circulars
    - Audit event count since last review
  ↓
  CA reviews (blocked if any items FAIL)
    - Identifies: retention_years=10 ✓
    - Identifies: vat_method = DEDUCTION ✓ (matches tax reg card)
    - Identifies: COA matches TT200 ✓
    - Identifies: all checks PASS
  ↓
  CA stamps: "I certify the system configuration is compliant as of 2026-04-15"
  System: sets legal_reviewed_at, legal_reviewed_by
  System: emits LEGAL_REVIEW_STAMPED event
  System: marks all unreviewed config changes as "sanctioned"
  ↓
  Schedule next review: 2027-Q2
  System sends calendar invitation to CA
```

**Failure handling:**
- Any FAIL item → System blocks stamp with 422; lists specific violations
- CA must remediate (update config / file with tax authority) before re-stamp

---

## Journey 06: Adding New E-Invoice Series (A Perspective)

**Persona:** Giám đốc
**Goal:** Add new series when "AA/2026" will be exhausted (15,000 invoices reached)

```
A monitors: Invoice Series Usage Dashboard
  Q3 2026: AA/2026 at 14,200 / 15,000 (94% utilization)
  A flags CA: "Need new series by end of Q3"
  CA: Declares "AB/2026" to GDT via thuedientu.gdt.gov.vn portal
  CA receives series approval from GDT (circular response)
  ↓
  A navigates: Settings → Invoice Series
  Current: AA/2026 (active, next_seq=14201), 1 active series
  ↓
  A: POST /invoice-series
    Body: { prefix: "AB/2026", ca_signer: "VNPT", declared_to_gdt_at: "2026-09-15" }
  ↓
  System: checks active count = 1 < 15; adds AB/2026 with active=True, next_seq=1
  System: adds second series - now 2 active (≤15 config shows max)
  System: emits INVOICE_SERIES_ADDED audit event
  ↓
  In Q4: CA decides to stop using AA/2026
  A: PATCH /invoice-series/AA/2026 { active: false }
  System: AA/2026 marked inactive; history preserved
  Next sequence: AB/2026-00001 (begins immediately)
  ↓
  Sequence log preserves: AA/2026 used 14,501 invoices (auditable)
```

---

## Journey 07: Negative Path — Failed Period Lock Attempt

**Persona:** Kế toán viên (SA) trying to circumvent period lock

```
Last day of March, CA has LOCKED March 2026
  SA: "I forgot to post this March entry"
  SA attempts: POST voucher dated 2026-03-28 (locked period)
  → PeriodLockService.is_locked(company_id, "2026-03")
    → SQL: SELECT 1 FROM period_locks WHERE company_id=? AND lock_type IN ('PERIOD', 'FYEAR_CLOSED')
    → EXISTS = True
    → raise AccountingPeriodLockedError
  → System returns 403:
    { "error": "PERIOD_LOCKED",
      "message": "Kỳ kế toán tháng 3/2026 đã bị khóa. Không thể nhập chứng từ ngày hậu kỳ.",
      "locked_by": "CA user ID",
      "locked_at": "2026-03-31T17:30:00Z" }
  ↓
  SA escalates to CA
  CA: assesses; determines this is a legitimate correction
  CA procedure:
    1. CA documents justification in notes field
    2. CA unlocks period (if company policy allows; FYEAR_CLOSED does NOT)
    3. SA reposts entry dated 2026-03-28
    4. CA re-locks period
    5. AUDIT: PERIOD_UNLOCKED event emitted (reviewed at next quarterly access review)
  ↓
  Audit trail: 2 unlocks in lifetime → flag for deeper review in annual legal review
```

**Learning:** Lock/unlock cycle visible in audit; pattern of repeat unlocks flags to CA and auditor.