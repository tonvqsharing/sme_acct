# Business Requirements Document: Chart of Accounts (COA) Module
## Vietnamese SME Accounting Application — v2026

**Document Status:** DRAFT — v1.0  
**Date:** 2026-08-18  
**Prepared by:** BA Lead (20+ years experience) & Chief Accountant (20+ years experience)  
**Alignment:** Circular 99/2025/TT-BTC (effective 01/01/2026), Circular 200/2014/TT-BTC, Circular 133/2016/TT-BTC  
**Codebase:** Flask + Clean Architecture, src/domain/entities/, src/infrastructure/database/models.py

---

## 1. Executive Summary

This BRD defines the Chart of Accounts (COA) module for the Vietnamese SME accounting application. The module must comply with Vietnam's new Accounting Regime per **Circular 99/2025/TT-BTC** (effective 01/01/2026), which replaces Circular 200/2014/TT-BTC and modifies Circular 133/2016/TT-BTC.

The COA module is a core financial management component that:
- Maps to the 9 main account categories per Vietnamese Accounting Standards (VAS)
- Supports both the new TT99 regime and legacy TT200/TT133 structures
- Enables enterprise-customizable COA within legal boundaries
- Integrates with vouchers, invoices, bank reconciliation, tax reporting, and financial statement generation
- Provides audit trails, data integrity, and configurable account tags for analytical reporting

**Business Impact:** A properly structured COA is the foundation for all accounting operations — voucher entry, financial reporting, tax declaration (VAT/CIT/PIT), and regulatory compliance. Errors in COA design cascade into misstated financials, failed tax filings, and audit findings.

---

## 2. Stakeholders & Roles

| Role | Responsibilities | Authority |
|---|---|---|
| **CHIEF ACCOUNTANT** (20+ years exp.) | Approves COA structure, account codes, internal accounting regulation; accountable to tax authorities | Final sign-off on account creation/modification |
| **ACCOUNTANT** (5+ years exp.) | Daily voucher entry, account selection, month-end closing, report generation | Creates/edits vouchers within approved COA |
| **FINANCE MANAGER** | Oversees COA design, analytical reporting, consolidation; reviews periodic COA health | Budget authority; can request COA restructuring |
| **CEO/EXECUTIVE** | Legal entity accountability; approves accounting policy (IGAP) | Ultimate accountability; signs off accounting regulation |
| **IT/DEVELOPER** | Implements COA changes in software, maintains audit trails, ensures data integrity | Technical execution; follows accounting policy |

---

## 3. Regulatory Framework

### 3.1 Primary Legal Basis

| Law/Circular | Effective Date | Scope | Key COA Provisions |
|---|---|---|---|
| **Law on Accounting 2015 (amended 2022)** | 01/01/2016 | All enterprises in Vietnam | Chapter IV: Chart of Accounts; mandatory account structure; audit trail requirements |
| **Circular 200/2014/TT-BTC** | 01/01/2015 | All enterprises | Prescriptive COA with 9 main categories, 76 Level-1 accounts, 71 Level-2 accounts; account codes: 2-digit or 3-digit prefixes |
| **Circular 133/2016/TT-BTC** | 01/01/2017 | Small & medium enterprises | Simplified COA; may use TT200 subset or adapt with documented justification |
| **Circular 99/2025/TT-BTC** | **01/01/2026** | **All enterprises (mandatory replacement of Circular 200)** | **Principle-based COA:** enterprises define own account structure within VAS framework; must document in IGAP; supports IFRS convergence; removes rigid templates |

### 3.2 Compliance Requirements

| Requirement | Detail | Enforcement |
|---|---|---|
| **Account Code Format** | `^\d{10}$` or `^\d{10}-\d{3}$` (Vietnamese MST); per TT99: `^[1-9]\d{2}$` or `^[1-9]\d{3}$` (Vietnamese chart of accounts) | SQL constraint; domain validation |
| **9 Main Categories** | Assets, Receivables, Inventory, Fixed Assets, Payables, Accrued Expenses, Revenue, Operating Expenses, undistributed profit | Must be present in COA; reordering allowed with IGAP documentation |
| **Account Tagging** | Each account auto-tagged with reporting line (e.g., "Revenue", "Tax payable", "Fixed assets") | Mandatory for VAT/CIT/PIT report generation |
| **Audit Trail** | All COA changes logged: who, when, what changed, reason; immutable log per Law on Accounting §19 | db.session.commit() + event append; SHA-256 checksum chain (PeriodLockEvent pattern) |
| **Software Certification** | Accounting software must comply with Law on Accounting, Tax Law, and not alter fundamental accounting principles/Methods; must not impact figures in books/FS; must ensure accuracy, transparency, traceability, chronological correction logging, confidentiality, security, upgradeability, interoperability with e-invoicing | GDT validation; annual software audit |
| **IGAP (Internal Accounting Policy)** | Must document: functional currency decision, account mapping, approval workflows, customizations, reasons for deviations from standard COA | Required for compliance; reviewed by tax authorities |

---

## 4. module Scope

### 4.1 In-Scope Features

| Feature | Description | Priority |
|---|---|---|
| **COA Creation & Editing** | Add new accounts, modify account names/codes/structure; guided workflow requiring Chief Accountant approval; support TT99 and legacy COA import/export | Must |
| **Account Categorization** | Assign each account to one of 9 main categories; sub-categorization with user-defined groups | Must |
| **VAT Rate Mapping** | Map accounts to VAT rates: 0%, 5%, 8%, 10%; auto-tax-total calculation per voucher entry | Must |
| **Account Tags (Analytic Tags)** | Pre-defined tags for financial statement lines: "Revenue", "Tax payable", "Fixed assets", "Inventory", "Cost of goods sold", "Operating expense", "Cash", "Bank", "Undistributed profit" | Must |
| **Report Line Tagging** | Each account maps to specific financial statement report lines per Circular 99 Appenix IV | Must |
| **COA Import/Export** | XML/JSON export/import for backup, migration, multi-company rollout; preserve account IDs, codes, tags | Should |
| **Opening Balance Setup** | Initial COA setup at first FY start; map opening balances to each account; validate against trial balance | Must |
| **Period Closing & Reclassification** | Auto-reclassification entries at period end (e.g., VAT output→payable, retained earnings); reversible with reason | Must |
| **Multi-company / Tenant Isolation** | Per-company COA; shared master COA with per-company overrides; company_id FK on all account rows | Could (post-v2) |
| **E-invoice Integration** | Auto-suggest account on e-invoice line item creation; validate account-code-format on upload; link to VAT declaration | Should |

### 4.2 Out-of-Scope (Deferred to v2)

- Multi-company consolidation / group-level COA (company isolation pending — see AGENTS.md "research report flags 7 critical gaps")
- Advanced costing methods (job costing, BOM costing) — land with inventory module
- Multi-currency revaluation at account level (covered by Currency module D4)
- AI-assisted account coding — v3

---

## 5. Functional Requirements

### 5.1 Account Management

| ID | Requirement | Priority | Error Handling |
|---|---|---|---|
| **FR-01** | System shall provide COA CRUD (Create, Read, Update, Delete) with Chief Accountant approval flag | Must | Validation error if non-CHIEF_ACCOUNTANT attempts deletion of system accounts |
| **FR-02** | Each account shall have: code (10-digit or 10-digit-3digit), name, category (9 main types), status (Active/Closed), account tags, VAT rate mapping, report line tag | Must | Reject account creation if code format invalid per `^\d{10}$` or `^\d{10}-\d{3}$`; reject if code already exists |
| **FR-03** | Accounts classified as "System" (pre-loaded per TT99/TT200) shall be read-only; modifiable only via migration module with reason and audit log | Must | Return 403 Forbidden with error code "COA_SYSTEM_ACCOUNT" if non-admin attempts mod |
| **FR-04** | Support import of standard COA: TT99 (new regime) and TT200/TT133 (legacy); mapping flags for each imported account | Must | Silent skip of duplicates; log imported count vs skipped count |
| **FR-05** | Account status tracking: Active, Closed, Suspended; Closed accounts不可用 in new voucher entries but retained in history | Must | Prevent selection of Closed account in voucher line; allow history view |

### 5.2 VAT & Tax Reporting

| ID | Requirement | Priority |
|---|---|---|
| **FR-06** | Each account must have exactly one VAT rate mapping: 0%, 5%, 8%, or 10%; default per enterprise regime | Must |
| **FR-07** | System shall auto-compute VAT totals per voucher: `subtotal * rate`; accumulate per account across all vouchers in period | Must |
| **FR-08** | Generate trial balance per account with opening/closing balances, total debit, total credit, VAT amount; export to CSV/PDF | Must |
| **FR-09** | Produce VAT declaration register: output VAT (sales), input VAT (purchases), net VAT per rate; match HTKK XML format | Must |
| **FR-10** | Map accounts to CIT/PIT report lines per Circular 09/2015/TT-BTC (amended); auto-populate corporate income tax declaration | Should |

### 5.3 Account Tags & Analytical Reporting

| ID | Requirement | Priority |
|---|---|---|
| **FR-11** | System shall provide 7 mandatory account tags: Revenue, Tax Payable, Fixed Assets, Inventory, COGS, Operating Expense, Undistributed Profit | Must |
| **FR-12** | Enterprises may add custom account tags beyond the 7 mandatory; each custom tag must be documented in IGAP | Should |
| **FR-12b** | Every account must have at least 1 tag (mandatory or custom); un-tagged accounts rejected in COA creation | Must |
| **FR-13** | Report generation shall filter by account tag, category, VAT rate, date range, company_id | Must |

### 5.4 Audit & Compliance

| ID | Requirement | Priority |
|---|---|---|
| **FR-14** | All COA changes logged: `account_id`, `old_code`, `new_code`, `old_name`, `new_name`, `changed_by` (UUID), `changed_at` (UTC), `reason`; immutable via SHA-256 checksum chain | Must |
| **FR-15** | COA change requires Chief Accountant role (`@casbin_required(*FY_ADMIN_ROLES)` pattern) + written reason; reason stored in audit log | Must |
| **FR-16** | System shall prevent deletion of accounts with existing voucher history; archive account (status=Closed) instead | Must |
| **FR-17** | Support COA versioning: each COA change creates a new version; prior version retained for audit 10-year retention per Law on Accounting | Should |

---

## 6. Non-Functional Requirements

| Requirement | Detail |
|---|---|
| **Performance** | COA lookup by code: ≤50ms; list by company: ≤200ms for typical SME (≤200 accounts) |
| **Security** | Domain layer MUST stay free of sqlalchemy/web imports; COA entities free of Flask/SQLAlchemy; `@casbin_required` on all COA routes; AUDITOR read-only |
| **Data Integrity** | Account code uniqueness per company; no orphan accounts (every account belongs to a category); referential integrity with vouchers |
| **Extensibility** | New account tags addable without code change via admin UI + IGAP documentation; VAT rates configurable per enterprise regime |
| **Compatibility** | TT99 compliant out-of-box; TT200/TT133 import supported; IFRS convergence roadmap (v2.1) |
| **LSP Safety** | No mypy/ruff red on new files; follow existing patterns (ports, repo, service) |

---

## 7. Interface Requirements

### 7.1 API Endpoints (REST-ish, following currencies_bp pattern)

| Method | Path | Description | Role |
|---|---|---|---|
| `GET` | `/api/v1/coa/accounts` | List accounts with pagination, filter by category, tag, VAT rate, status | READ_ROLES |
| `POST` | `/api/v1/coa/accounts` | Create new account; requires CHIEF_ACCEPTANT + reason | CHIEF_ACCOUNTANT/ADMIN/DIRECTOR |
| `GET` | `/api/v1/coa/accounts/{id}` | Get account detail with audit history | READ_ROLES |
| `PATCH` | `/api/v1/coa/accounts/{id}` | Update account name/code/tags; requires CHIEF_ACCOUNTANT | CHIEF_ACCOUNTANT/ADMIN/DIRECTOR |
| `DELETE` | `/api/v1/coa/accounts/{id}` | Archive account (soft-delete); requires CHIEF_ACCOUNTANT | CHIEF_ACCOUNTANT |
| `GET` | `/api/v1/coa/categories` | List 9 main categories with account count per category | READ_ROLES |
| `GET` | `/api/v1/coa/tags` | List all account tags (mandatory + custom) | READ_ROLES |
| `GET` | `/api/v1/coa/vat-rates` | List configurable VAT rates per enterprise regime | READ_ROLES |
| `POST` | `/api/v1/coa/import` | Import COA from XML/JSON (TT99/TT200 template); dry-run mode | CHIEF_ACCOUNTANT |
| `GET` | `/api/v1/coa/export` | Export current COA to XML/JSON | READ_ROLES |

### 7.2 Admin UI Routes (planned v2)

- `/coa/manager` — visual COA tree editor
- `/coa/import-export` — upload/download templates
- `/coa/report-lines` — map accounts to report lines

---

## 8. Data Model Design (High Level)

### 8.1 Core Entities (Domain Layer — NO sqlalchemy/web imports)

| Entity | Key Attributes | Relationships |
|---|---|---|
| **Account** | `id` (UUID), `code` (str, 10-digit), `name` (str), `category` (Enum: Asset/Receivable/Inventory/FixedAsset/Payable/AccruedExpense/Revenue/OperatingExpense/UndistributedProfit), `status` (Enum: Active/Closed/Suspended), `vat_rate` (Decimal 5,2: 0/5/8/10), `account_tags` (list of Tag Enum), `report_line` (str, per Appendix IV), `parent_id` (UUID, self-referencing for sub-accounts), `company_id` (FK), `created_by` (UUID), `created_at` (UTC), `updated_at` (UTC), `audit_checksum` (str SHA-256) | FK → Company; self-referencing FK → parent Account; 1:N → VoucherLine; 1:N → AuditLog |
| **AccountCategory** | `id`, `name` (e.g., "Current Assets"), `code_prefix` (e.g., "1."), `order_index` (int), `is_system` (bool) | 1:N → Account |
| **AccountTag** | `id`, `name` (e.g., "Revenue"), `code` (e.g., "REV"), `is_mandatory` (bool), `report_line` (str) | 1:N → Account |
| **COAVersion** | `id`, `version_num` (int), `effective_date` (date), `is_active` (bool), `change_reason` (str), `changed_by` (UUID), `checksum` (str SHA-256) | 1:N → Account (snapshot) |

### 8.2 Database Models (Infra Layer)

- `AccountModel` (SQLAlchemy 2.0 DeclarativeBase)
  - Enum: `AccountCategory` (9 values), `AccountStatus` (Active/Closed/Suspended)
  - Unique constraint: `(company_id, code)`
  - Index: `company_id + category + status`
  - Relationships: `company`, `parent`, `voucher_lines`, `audit_events`
- `AccountTagModel`
  - Unique: `(company_id, code)`; `is_mandatory` flag
- `COAVersionModel`
  - Tracks version chain; each change adds row; 10-year retention

### 8.3 Repository Port (application/ports/__init__.py)

- `AccountRepositoryPort` with: `get_by_id`, `get_by_code`, `list_by_company`, `list_by_category`, `search_by_tag`, `create`, `update`, `soft_delete`, `get_version_history`
- `AccountCategoryRepositoryPort` with: `get_system_categories`, `list_all`
- `AccountTagRepositoryPort` with: `get_mandatory`, `list_by_company`, `create`

---

## 9. Workflows & Processes

### 9.1 COA Creation Workflow

```
1. CHIEF_ACCOUNTANT initiates "Create Account"
   → System validates code format (^\d{10}$ or ^\d{10}-\d{3}$)
   → System checks code uniqueness per company_id
   → System validates category is one of 9 main types
   → System assigns default VAT rate per enterprise regime
   → System suggests account_tags: at least 1 mandatory tag
   → System requires written reason (max 500 chars)
   → CHIEF_ACCOUNTANT submits → system records audit event (SHA-256 chain)
   → Account created with status=Active

2. (Optional) Import COA
   → Upload TT99 or TT200 template XML/JSON
   → System maps each row to Account entity
   → Duplicate codes: skip + log
   → New codes: create
   → System generates audit event for each account created/skipped
   → CHIEF_ACCOUNTANT reviews import summary → activate version
```

### 9.2 Account Modification Workflow

```
1. User requests account update
   → System checks: account has no associated voucher lines (if yes → reject with "Cannot modify: existing voucher history")
   → If OK: system creates COAVersion snapshot (current state → history)
   → System allows code/name/tags/VAT rate change
   → CHIEF_ACCOUNTANT approves change with reason
   → Audit event appended: old_value → new_value, by whom, why
   → Version incremented; prior version retained 10 years

2. (Prohibited) Deletion of account with voucher history
   → System: soft-delete → status=Closed; account hidden from active COA
   → All historical vouchers retain reference to closed account code
   → Report generation: option to include/exclude Closed accounts
```

### 9.3 VAT Declaration Workflow

```
1. Select period (month/quarter/year)
2. System auto-aggregates per account:
   - Total debit, total credit (tol 0.01)
   - VAT output: sum of (subtotal * vat_rate) for rate=10%/5%/8%/0% sales accounts
   - VAT input: sum of (subtotal * vat_rate) for rate-purchase accounts
   - Net VAT per rate = output - input
3. System generates VAT register report:
   - Format: per Circular 78/2012/TT-BTC (VAT declaration)
   - XML output matching HTKK portal expected format
   - Includes: enterprise info, period, account mappings, total amounts
4. CHIEF_ACCOUNTANT reviews → approves → system marks period VAT-locked
5. System locks COA for that period (no further changes without reversal entry)
```

### 9.4 Period Closing & Reclassification

```
1. All vouchers for period must be POSTED (status=POSTED)
2. System validates: every voucher debit+credit balanced (tol 0.01)
3. Auto-reclassification entries (if configured):
   - Accrued expenses → recorded expenses
   - Prepaid revenue → recognized revenue
   - VAT adjustments (output→input corrections)
4. System creates reclassification vouchers with reason
5. CHIEF_ACCOUNTANT reviews reclassification entries
6. Period status → CLOSED; COA version locked for that period
7. Opening balances for next period auto-derived from prior period trial balance + reclassification totals
```

---

## 10. Exception Paths & Edge Cases

| Scenario | Behavior | Error Code |
|---|---|---|
| **E-01** | User creates account with code `AB12345678` (invalid format) | 422 VALIDATION_ERROR; "Account code must be 10 digits (^\d{10}$) or 10-digit-grouped (^\d{10}-\d{3}$)" |
| **E-02** | User creates account with code already existing per company | 409 CONFLICT; "Account code already exists for this company" |
| **E-03** | User attempts to modify system (TT99 pre-loaded) account | 403 FORBIDDEN; "System account requires migration module" |
| **E-04** | User attempts to delete account with existing voucher history | 409 CONFLICT; "Cannot delete: account has voucher history. Close account instead" |
| **E-05** | User creates account without any account tag | 422 VALIDATION_ERROR; "At least 1 account tag is mandatory" |
| **E-06** | User creates account with VAT rate not matching enterprise regime | 422 VALIDATION_ERROR; "VAT rate must match enterprise regime: 0%/5%/8%/10%" |
| **E-07** | COA import: duplicate account codes across template rows | System: skip duplicate, log "Code X skipped: already exists"; continue processing |
| **E-08** | User generates VAT report for period with unposted vouchers | 400 BAD_REQUEST; "Period contains unposted vouchers; post all vouchers before generating VAT report" |
| **E-08b** | User attempts VAT report for period > 10 years old | 410 GONE; "Period beyond 10-year retention; cannot generate report; request data archive" |
| **E-09** | Enterprise changes accounting regime (Circular 200 → Circular 99) | System: import TT99 template; map legacy accounts → new structure; create COAVersion; mark old version "historical"; all existing vouchers remain linked to old account codes for 10 years |
| **E-10** | Enterprise requests custom account tag beyond 7 mandatory | System: create tag with `is_mandatory=False`; add to IGAP documentation requirement; warn: "Custom tag not auto-mapped to report lines; manual mapping required for tax declarations" |

---

## 11. User Journeys

### 11.1 Chief Accountant: Initial COA Setup (New Company / New FY per Circular 99)

**Pre-conditions:** Company registered in system; enterprise regime selected (TT99 or TT200/TT133); IGAP documented.

**Step-by-step:**

1. **Login** as Chief Accountant → role check `@casbin_required(*FY_ADMIN_ROLES)`
2. **Navigate** to COA Manager → system shows empty COA or TT99 default template
3. **Select regime:** TT99 (recommended) or TT200/TT133 (legacy)
4. **Import COA** (if legacy): upload TT200/TT133 XML → system maps accounts; for each: code, name, category, VAT rate, tags → review import summary → approve
5. **Add custom accounts:** as needed for business (e.g., "Display equipment", "Contract asset"); each requires tag assignment + VAT rate + reason
6. **Map report lines:** each account → Appendix IV report line code (e.g., "1.1" for "Cash", "2.1" for "Trade receivables")
7. **Set opening balances:** for each account, enter opening debit/credit (trial balance); system validates sum debit ≈ sum credit (tol 0.01)
8. **Save COA version:** system creates COAVersion v1.0 with checksum; all prior versions archived
9. **Begin first FY:** system enables voucher entry with COA-validated account selection

**Post-conditions:** COA active; all accounts tagged; VAT rates configured; audit log has entry for setup; enterprise compliant with Circular 99 from Day 1.

### 11.2 Accountant: Daily Voucher Entry

1. **Login** as Accountant → role check (`@casbin_required(*READ_ROLES)` + voucher-type specific)
2. **Create Voucher** → system presents COA dropdown per account code
3. **Account Selection:** Account must be Active; if Closed → system blocks selection with message: "Account closed; select active account or reopen"
4. **VAT Rate:** System auto-selects VAT rate based on account mapping; accountant can override with reason (audited)
5. **Lines Entry:** Each line → account code, description, debit, credit (balanced: tol 0.01)
6. **System Validation:**
   - Account code format valid
   - VAT rate matches account mapping (or overridden with reason)
   - At least 1 line tagged with appropriate analytic tag
   - Total debit ≈ total credit (tol 0.01)
7. **Post Voucher:** system updates account balances (debit/credit accumulators); appends audit event; updates trial balance
8. **Save:** voucher status → POSTED; period trial balance auto-updated

### 11.3 Finance Manager: Monthly COA Review

1. **Login** as Finance Manager → role check
2. **Generate Trial Balance Report:** per account with opening/closing balances, total D/C, VAT per account
3. **Filter by:** account tag, category, VAT rate, date range, company_id
4. **Identify anomalies:** negative balances in asset accounts, untagged accounts, VAT rate mismatches
5. **Request COA modifications:** submit CHIEF_ACCOUNTANT request with reason
6. **Export COA snapshot:** CSV/PDF for internal review; archive with version number

### 11.4 Chief Accountant: Period-End COA Close

1. **Verify:** all vouchers POSTED for period; trial balance balanced
2. **Generate VAT declaration register** (auto, per FR-09)
3. **Generate reclassification entries** if accrued/prepaid items exist
4. **Create reclassification vouchers** with reason → CHIEF_ACCOUNTANT approves
5. **Lock COA version** for period: system increments COAVersion; prior version read-only; no further account changes without reversal voucher
6. **Set period status** → CLOSED; open new period with opening balances auto-derived
7. **Archive:** all audit events for period retained 10 years per Law on Accounting §21

---

## 12. Templates & exports

| Template | Format | Contents | When Generated |
|---|---|---|---|
| **COA Import Template (TT99)** | XML | `<account><code>1001000001</code><name>Cash</name><category>Asset</category><vat_rate>0</vat_rate><tags><tag>Cash</tag></tags><report_line>1.1</report_line></account>` | New company setup; regime switch |
| **COA Import Template (TT200)** | XML | Legacy format; system maps old codes → new if needed | Legacy migration |
| **COA Export Snapshot** | JSON / CSV | All accounts: id, code, name, category, status, vat_rate, tags, report_line, created_by, created_at, version_num | Month-end close; audit |
| **VAT Declaration Register** | XML | Per HTKK format: enterprise info, period, output VAT per rate, input VAT per rate, net VAT, account mappings | Monthly VAT filing |
| **Trial Balance Report** | CSV / PDF | Per account: code, name, opening_debit, opening_credit, closing_debit, closing_credit, total_debit, total_credit, vat_amount | Monthly/Quarterly/Yearly close |
| **COA Change Audit Log** | TXT / PDF | All changes per version: what, by whom, when, reason; SHA-256 checksum verification | Annual audit |

---

## 13. Integration Points

| Integration | Direction | Description |
|---|---|---|
| **Voucher Module** | COA → Voucher | Every voucher line requires valid account code; system validates account status, category, VAT rate at line entry |
| **Invoice Module** | COA → Invoice | Invoice items default account per product/service category; VAT rate auto-mapped |
| **Currency/Exchange Rate** | COA → Currency | Accounts with foreign currency transactions mapped to specific currency; revaluation entries use account code filter |
| **Payroll/BHXH** | COA → Payroll | Employee benefit, social insurance, salary expense accounts mapped; auto-post to general ledger |
| **Audit Log** | COA → Audit Log | Every COA change appends event (PeriodLockEvent-pattern SHA-256 chain); every voucher post appends event |
| **E-Invoice** | COA → E-Invoice | Auto-suggest account on e-invoice line creation; validate account code format on upload; link to VAT declaration |
| **Reporting/BI** | COA ↔ Reporting | All financial reports (trial balance, P/L, B/S, VAT, CIT) filtered/aggregated by account code/category/tag/VAT rate |

---

## 14. Success Criteria (Definition of Done)

| Criterion | Target | Measurement |
|---|---|---|
| **COA Compliance** | 100% of accounts conform to Circular 99/2025 or documented legacy mapping | Audit of account catalog vs TT99 template |
| **VAT Accuracy** | VAT totals per report match HTKK XML within 0.01 VND | Test: generate VAT report → compare with GTĐ declaration |
| **Account Tag Coverage** | ≥95% of accounts have at least 1 mandatory tag | Catalog review |
| **Audit Trail Completeness** | 100% of COA changes have audit event with SHA-256 checksum | Automated test: mutate account → verify log entry |
| **Import Success Rate** | TT99 import: ≥95% accounts created successfully; duplicates skipped with log | Test import of sample TT99 template |
| **Performance** | COA list by company: ≤200ms for ≤200 accounts; account lookup by code: ≤50ms | Load test with 500 accounts |
| **Security** | No SQL injection via account code; no unauthorized COA modification; `@casbin_required` enforced | Pentest + code review |
| **Usability** | Chief Accountant can complete initial COA setup within 2 hours (new company) | UAT with target user |

---

## 15. Roadmap & Versioning

| Version | Key Deliverables | Target |
|---|---|---|
| **v1.0 (This BRD)** | Core COA module: CRUD, 9 categories, VAT rate mapping, 7 mandatory tags, audit trail, TT99 compliance, API + serializer, unit+integration tests | 2026-09 (after this BRD approval) |
| **v1.1** | COA import/export (TT99/TT200 templates); period closing reclassification entries; VAT declaration XML export | 2026-11 |
| **v1.2** | Custom account tags (beyond 7 mandatory); report line mapping editor; multi-company COA overrides (per-company) | 2027-02 |
| **v2.0** | Group-level COA consolidation; IFRS convergence enhancements; AI-assisted account coding suggestion (human-validated) | 2027-09 (post-ledger-module) |

---

## 16. Approval & Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| **BA Lead** | (20+ years BA experience) | _________________ | 2026-08-18 |
| **Chief Accountant** | (20+ years accounting, VAS compliance) | _________________ | 2026-08-18 |
| **CEO/Executive** | (Legal entity accountability) | _________________ | 2026-08-18 |

---

*End of BRD*

---

**Next Step:** Upon BRD approval, proceed to Technical Specifications (specs-tdd.md) detailing domain entities, repository ports, service layer, REST API blueprint, database migration, and test plan. All domain code must stay free of sqlalchemy/web imports (per Clean Architecture rules).

**Reference Materials (read alongside):**
- `docs/fiscal-year-period/` — already implemented FY module (patterns to reuse)
- `docs/currencies-exchange/` — service pattern (Service sans Flask/SQLAlchemy)
- `AGENTS.md` — RBAC, coding conventions, testing strategy
- `docs/CODING_CONVENTION.md` — naming, layer boundaries, commit format
- `Law on Accounting 2015` (Vietnamese original) — audit trail, 10-year retention, software certification
- `Circular 99/2025/TT-BTC` full text — COA structure, report lines, account codes
- `Circular 200/2014/TT-BTC` — legacy COA (for import/mapping)
- `Circular 133/2016/TT-BTC` — SME simplified COA