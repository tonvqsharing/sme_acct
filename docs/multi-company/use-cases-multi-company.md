# Use Cases — Multi-Company / Master-Module
> v0.1 | Status: DRAFT | Derives from: docs/brd-multi-company.md, docs/specs-multi-company.md

---

## UC-0001: Create Subsidiary Company

**Actor:** Group CFO (GROUP_CFO)  
**Pre:** User authenticated; at least one master company exists  
**Post:** New company record active in system

### Happy Path
1. CFO navigates to **Companies → Create Subsidiary**
2. System shows form: Name, Legal Name, MST, Tax Agency, Regime, FY Start, COA template
3. CFO fills valid MST (10 digits or `XXXXXXXXXX-XXX`)
4. CFO selects accounting regime (Micro / SME / Enterprise)
5. CFO selects COA template (default or custom)
6. CFO submits
7. System validates: MST unique, COA valid per regime, fiscal year not before master FY
8. System creates Company record with `status=ACTIVE`, `parent_company_id=<master>`
9. System creates audit log entry
10. System redirects to company detail

### Alternative Paths
- **A1: Copy master COA** — CFO checks "Copy COA from parent"; system copies chart instead of default
- **A2: Import initial balances** — CFO uploads opening balance CSV; system validates against COA before posting

### Exception Paths
- **E1: MST_TAKEN** — System shows "MST already in use"; form retains input; suggest activating deactivated company
- **E2: INVALID_MST** — System shows "Mã số thuế không hợp lệ. VD: 10 chữ số hoặc XXXXXXXXXX-XXX"
- **E3: INVALID_COA_CODE** — System shows "Mã tài khoản 'XXX' không hợp lệ. VD: 111, 511"
- **E4: FISCAL_YEAR_MISMATCH** — System warns subsidiary FY must not precede parent FY by more than 1 year (configurable)

---

## UC-0002: Assign Bookkeeper to Company

**Actor:** Group CFO or SysAdmin  
**Pre:** Company exists; user account exists  
**Post:** User has SUBSIDIARY_BOOKKEEPER role scoped to company

### Happy Path
1. CFO opens **Company Settings → Users**
2. System shows users not yet assigned to this company
3. CFO selects user + role (Bookkeeper / Manager)
4. CFO confirms
5. System creates company-user mapping
6. User logs in next session; sees only assigned companies

### Alternative Paths
- **A1: Bulk assign** — CFO selects multiple users; assigns same role to all

### Exception Paths
- **E1: USER_ALREADY_ASSIGNED** — System shows "User already has role in this company"; skip
- **E2: LAST_ADMIN** — System blocks removal of last MASTER_ADMIN from master company

---

## UC-0003: Post Invoice to Subsidiary

**Actor:** Subsidiary Bookkeeper  
**Pre:** User authenticated; assigned to company A; company active  
**Post:** Invoice created with `company_id=A`; balances recalculated

### Happy Path
1. Bookkeeper selects company A from company switcher
2. Bookkeeper navigates to **Invoices → Create**
3. System pre-fills company=A; MST of company A shown on form
4. Bookkeeper enters invoice details + items
5. On "Add Item": system recalculates subtotal/VAT/grand_total (per domain rule)
6. Bookkeeper submits
7. System validates: MST tag matches company; tax fields per company's tax agency
8. System creates Invoice with `company_id=A`; `partner` scoped to company A
9. System shows confirmation

### Alternative Paths
- **A1: Create from existing partner** — Bookkeeper selects partner from company-scoped list

### Exception Paths
- **E1: COMPANY_INACTIVE** — System shows "Company is inactive"; redirects
- **E2: PERIOD_LOCKED** — System shows "Period locked for company A"; cannot post
- **E3: MST_MISMATCH** — Invoice's `partner_tax_id` MST conflicts with company MST block

---

## UC-0004: Period-End Close (Subsidiary)

**Actor:** Subsidiary Bookkeeper  
**Pre:** All invoices/vouchers posted for period; company active  
**Post:** Period locked; master notified TB available

### Happy Path
1. Bookkeeper navigates to **Period Close** for company A
2. System shows trial balance pre-check
3. Bookkeeper confirms
4. System runs trial balance check; reports any unbalanced vouchers
5. Bookkeeper resolves flagged items
6. Bookkeeper submits close
7. System: creates period lock record; sets `is_closed=True` on fiscal year period
8. System: publishes event "PeriodClosed: company=A, period=2025-01"
9. System: notifies master CFO that TB is available for consolidation

### Alternative Paths
- **A1: Force close with adjustment** — Manager approves, then bookkeeper force-closes (system records adjustment entry)

### Exception Paths
- **E1: UNBALANCED_VOUCHER** — "Voucher VCH-001 not balanced: Nợ=..., Có=..."; block close
- **E2: UNPOSTED_INVOICE** — "3 invoices in DRAFT"; block close
- **E3: ALREADY_CLOSED** — "Period already locked"; redirect

---

## UC-0005: Consolidated BCTC Generation

**Actor:** Group CFO  
**Pre:** All subsidiaries for group locked for period; at least one subsidiary active  
**Post:** Consolidated BCTC generated; draft status

### Happy Path
1. CFO opens **Consolidation → Generate BCTC** for group G
2. System shows available periods (all subsidiaries must be locked for that period)
3. CFO selects period (e.g., 2025-01 to 2025-12)
4. System creates ConsolidationRun; status=DRAFT
5. System pulls adjusted trial balance from each subsidiary
6. System shows combined trial balance
7. CFO adds master adjusting entries (if any): NST, NLD eliminations
8. CFO clicks **Generate Consolidated BCTC**
9. System produces: BCTC TSCĐ, KQKD, LCTT, Thuyết minh
10. System sets run status=DRAFT; CFO can edit entries
11. CFO approves; system sets status=POSTED; locks run

### Alternative Paths
- **A1: Preview without running** — CFO previews draft TB from subsidiaries

### Exception Paths
- **E1: SUBSIDIARY_NOT_LOCKED** — "Company X period not locked"; lists unlockeds
- **E2: ELIMINATION_IMBALANCE** — "Elimination entries do not balance: Nợ ≠ Có"; refuse to approve
- **E3: NO_SUBSIDIARIES** — "Group has no active companies"; abort

---

## UC-0006: Intercompany Invoice (Optional)

**Actor:** Subsidiary Bookkeeper  
**Pre:** Both entities active; user assigned to both (or delegation)  
**Post:** Invoice created; flagged `is_intercompany=True`; both sides tracked

### Happy Path
1. Bookkeeper (company A) creates invoice for customer = company B
2. System recognizes MST of company B matches internal registry
3. System sets `is_intercompany=True`; stores counterpart `related_company_id=B`
4. Company B's bookkeeper sees invoice in their accounts payable
5. Both invoices flagged for elimination in consolidation

### Exception Paths
- **E1: SAME_COMPANY** — "Cannot issue intercompany invoice to same entity"
- **E2: COUNTERPART_NOT_ACTIVE** — "Recipient company is inactive"

---

## UC-0007: Role-Based Access Control Verification

**Actor:** Any user  
**Pre:** User assigned to 1+ companies with specific roles  

### Happy Path (Subsidiary Bookkeeper)
1. Bookkeeper logs in
2. System shows company switcher with exactly the companies they have access to
3. Bookkeeper selects company A
4. All API calls include `company_id=A` filter
5. Bookkeeper tries to access company B URL directly → 403

### Exception Paths
- **E1: NO_ASSIGNED_COMPANIES** — User sees "No companies assigned"; contacts admin

---

## UC-0008: Deactivate Subsidiary

**Actor:** Group CFO or SysAdmin  
**Pre:** No open periods; no pending tax filings  
**Post:** Company status=INACTIVE; no further postings allowed

### Happy Path
1. CFO navigates to Company Settings → Actions → Deactivate
2. System confirms "Deactivate Company X? This cannot be undone."
3. CFO confirms
4. System sets `status=INACTIVE`; `is_active=False`
5. System blocks new invoices/vouchers for this company

### Exception Paths
- **E1: OPEN_PERIOD_EXISTS** — "Company has 2 open periods. Close them first."
- **E2: PENDING_TAX_FILING** — "Tax filing for 2025-Q1 pending. Submission required before deactivation."

---

## UC-0009: Consolidation Audit Trail Review

**Actor:** Auditor  
**Pre:** At least one consolidation run in POSTED status  
**Post:** Auditor sees full history of all consolidated entries

### Happy Path
1. Auditor opens **Consolidation → Audit Trail** for run R
2. System shows chronological list:
   - Subsidiary TB snapshots (company, period, totals)
   - Master adjusting entries (user, timestamp, amounts, reason)
   - Elimination entries (type, amounts, matched with)
3. Auditor can export as PDF or CSV

### Exception Paths
- **E1: RUN_NOT_POSTED** — "Run is still in DRAFT; audit trail only available for POSTED runs"

---

## UC-0010: Master Adjusting Entry (NST/NLD Elimination)

**Actor:** Group CFO  
**Pre:** Consolidation run in DRAFT; subsidiaries locked  
**Post:** Adjusting entry added; trial balance recalculated

### Happy Path
1. CFO views draft consolidated trial balance
2. CFO clicks **Add Adjusting Entry**
3. CFO enters: Description, Debit Account, Credit Account, Amount
4. System validates: accounts exist in COA, entry balanced (within 0.01 tolerance)
5. System adds entry; marks run as "requires re-check"
6. CFO clicks **Recalculate**; system updates consolidated figures
7. CFO approves when balanced

### Alternative Paths
- **A1: Bulk elimination** — System suggests NST/NLD pairs based on intercompany invoices flagged in period

### Exception Paths
- **E1: UNBALANCED_ENTRY** — "Entry not balanced: Nợ ≠ Có within tolerance"
- **E2: ACCOUNT_NOT_IN_COA** — "Account 9999 not in chart of accounts"
- **E3: RUN_LOCKED** — "Run already approved; cannot modify"

---

## UC-0011: COA Configuration per Company

**Actor:** Group CFO or Subsidiary Manager  
**Pre:** Company active  
**Post:** COA updated; validation per Circular 99/2025

### Happy Path
1. User opens **Company → Chart of Accounts**
2. System shows current COA in tree (assets, liabilities, equity, revenue, expenses)
3. User adds new account: code, name, type, reporting category
4. System validates: `^[1-9]\d{2}([1-9]\d?)?$` format; no duplicate codes
5. System adds account; shows in tree

### Alternative Paths
- **A1: Copy master COA** — User selects copy from parent

### Exception Paths
- **E1: INVALID_CODE_FORMAT** — "Mã '012' không hợp lệ; phải bắt đầu bằng 1-9"
- **E2: DUPLICATE_CODE** — "Mã '511' đã tồn tại"

---

## UC-0012: Software Registration per Entity (Tổng cục Thuế)

**Actor:** SysAdmin or GROUP_CFO  
**Pre:** Company exists; MST registered with Tổng cục Thuế  
**Post:** Software registered for entity's MST

### Happy Path
1. Admin navigates to **Settings → Software Registration**
2. System lists companies without registration status
3. Admin selects company; enters registration details (serial, cert number)
4. System stores registration; e-invoices use company's serial
5. System checks registration against Tổng cục Thuế list (stub integration)

### Exception Paths
- **E1: MST_NOT_IN_TAX_LIST** — "MST not found on Tổng cục Thuế recognized list"

---

## Use Case Index

| ID | Name | Primary Actor | Priority |
|---|---|---|---|
| UC-0001 | Create Subsidiary Company | GROUP_CFO | Must |
| UC-0002 | Assign Bookkeeper to Company | GROUP_CFO | Must |
| UC-0003 | Post Invoice to Subsidiary | SUBSIDIARY_BOOKKEEPER | Must |
| UC-0004 | Period-End Close (Subsidiary) | SUBSIDIARY_BOOKKEEPER | Must |
| UC-0005 | Consolidated BCTC Generation | GROUP_CFO | Must |
| UC-0006 | Intercompany Invoice | SUBSIDIARY_BOOKKEEPER | Should |
| UC-0007 | Role-Based Access Verification | Any | Must |
| UC-0008 | Deactivate Subsidiary | GROUP_CFO | Should |
| UC-0009 | Consolidated Audit Trail Review | AUDITOR | Must |
| UC-0010 | Master Adjusting Entry (NST/NLD) | GROUP_CFO | Must |
| UC-0011 | COA Configuration per Company | SUBSIDIARY_MANAGER | Must |
| UC-0012 | Software Registration per Entity | SYSADMIN | Should |

--- END OF FILE ---
