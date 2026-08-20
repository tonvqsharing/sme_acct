# Templates — Bank & Cash Accounts Module

## 1. Overview

This document provides ready-to-use templates for the Bank & Cash Accounts module. Templates follow the same format as other module templates in this codebase (e.g., templates-currencies.md, templates-coa-module-2026.md, templates-fiscal-year-period.md).

All templates are designed to be:
- **Fill-in-the-blank**: Replace placeholder text with actual values
- **Format-compliant**: Match existing module templates
- **Law-compliant**: Vietnamese Accounting Law (Luật Kế toán 2015), Circular 99/2025/TT-BTC
- **Ready for immediate use**: Can be copied, edited, and used immediately

---

## 2. Available Templates

### 2.1 Bank Account Creation Template

**File:** `docs/bank-cash/templates/bank-account-creation-template.md`

```
# Bank Account Creation Request

**Date:** {{DATE}} (DD/MM/YYYY)  
**Prepared by:** {{PREPARED_BY_NAME}} ({{ROLE}}, UUID: {{ACTOR_UUID}})  
**Company:** {{COMPANY_NAME}} (ID: {{COMPANY_UUID}})  
**Approval Status:** Pending CHIEF_ACCOUNTANT approval  

## 1. Bank Account Details

| Field | Value | Validation |
|-------|-------|------------|
| **Bank Name** | {{BANK_NAME}} (e.g., VietinBank, Sacombank) | Required, max 100 chars |
| **Account Number** | {{ACCOUNT_NUMBER}} | Required, unique per company, max 30 chars |
| **Account Holder** | {{ACCOUNT_HOLDER}} | Required, max 255 chars |
| **Branch** | {{BRANCH}} (e.g., "Cục Thành Phố", "Chi nhánh Huyện") | Optional, max 200 chars, default "" |
| **Is Primary** | {{IS_PRIMARY}} (True/False) | Only one primary per company |

## 2. Business Justification

**Reason for new bank account:**
{{BUSINESS_REASON}}

**Expected benefits:**
{{EXPECTED_BENEFITS}}

**Transaction volume estimate (per month):**
{{TRANSACTION_VOLUME}}

## 3. SOD (Separation of Duties) Requirements

| Role | Action | Required | Reason |
|------|--------|----------|--------|
| **CHIEF_ACCOUNTANT** | Set as primary account | Yes | Primary account change affects all company financial reporting |
| **ACCOUNTANT** | Approve primary change | Yes | 2-actor SOD rule per company policy |
| **AUDITOR** | Review audit trail | Yes (read-only) | 10-year retention compliance |

## 4. Audit & Retention

- **Checksum Algorithm:** SHA-256 chaining (prev + actor + timestamp + action + reason + entity_id)
- **Retention Period:** 10 years minimum per Luật Kế toán 2015, Article 11
- **Destruction:** Requires formal request via /api/audit-log/destroy, Certificate of Destruction generated
- **Audit Events:** Created on: Account creation, primary change, any status modification

## 5. Sign-off

**Prepared by:** {{PREPARED_BY_SIGNATURE}} ({{ROLE}})

**Approved by (CHIEF_ACCOUNTANT):** {{CHIEF_SIGNATURE}} (UUID: {{CHIEF_UUID}})

**Approved by (ACCOUNTANT - 2nd SOD actor):** {{ACCOUNTANT_SIGNATURE}} (UUID: {{ACCOUNTANT_UUID}})

**Date:** {{SIGNING_DATE}}

---

### Usage:
1. Copy this template to a new file
2. Replace all {{PLACEHOLDERS}} with actual values
3. Print or submit via the SME Accounting App (POST /api/v1/bank-accounts)
4. Retain per 10-year retention policy

---

### 2.2 Cash Account Creation Template

**File:** `docs/bank-cash/templates/cash-account-creation-template.md`

```
# Cash Account Creation Request

**Date:** {{DATE}} (DD/MM/YYYY)  
**Prepared by:** {{PREPARED_BY_NAME}} ({{ROLE}}, UUID: {{ACTOR_UUID}})  
**Company:** {{COMPANY_NAME}} (ID: {{COMPANY_UUID}})  
**Approval Status:** Pending  

## 1. Cash Account Details

| Field | Value | Validation |
|-------|-------|------------|
| **Cash Code** | {{CASH_CODE}} | Required, TT99 format: ^[1-9]\d{2}$ or ^[1-9]\d{3}$ |
| **Cash Account Name** | {{CASH_NAME}} | Required, max 200 chars |
| **Opening Balance** | {{OPENING_BALANCE}} VND | Required, NUMERIC(18,2), ≥ 0 |
| **Is System** | {{IS_SYSTEM}} (True/False) | System accounts protected from modification |

## 2. Business Justification

**Purpose of cash account:**
{{PURPOSE}}

**Expected cash flow pattern:**
{{CASH_FLOW_PATTERN}}

**Maximum expected balance:**
{{MAX_BALANCE}}

## 3. TT99 Code Validation

**Format check:** ^[1-9]\d{2}$ or ^[1-9]\d{3}$  
**Example valid codes:** 111, 511, 6111, 999  
**Example invalid codes:** 011, -11, abc  

**Current code uniqueness:** Must be unique per company (DB constraint)

## 4. SOD (Separation of Duties) Requirements

| Role | Action | Required | Reason |
|------|--------|----------|--------|
| **CHIEF_ACCOUNTANT** | Create cash account | Yes (for amounts > threshold) | Large cash accounts require chief oversight |
| **ACCOUNTANT** | Record daily transactions | Yes (per transaction) | 2-actor SOD for cash movements |
| **AUDITOR** | Verify balance integrity | Yes (read-only) | 10-year retention compliance |

## 5. Audit & Retention

- **Checksum Algorithm:** SHA-256 chaining (same as bank accounts)
- **Retention Period:** 10 years minimum per Luật Kế toán 2015, Article 11
- **Balance Tracking:** current_balance = opening_balance + sum(all transactions)
- **Destruction:** Formal request required, Certificate of Destruction generated
- **Audit Events:** Created on: Account creation, balance update, closure, any transaction

## 6. Sign-off

**Prepared by:** {{PREPARED_BY_SIGNATURE}} ({{ROLE}})

**Approved by (CHIEF_ACCOUNTANT - if required):** {{CHIEF_SIGNATURE}} (UUID: {{CHIEF_UUID}})

**Date:** {{SIGNING_DATE}}

---

### Usage:
1. Copy this template to a new file
2. Replace all {{PLACEHOLDERS}} with actual values
3. The cash code must pass TT99 format validation: ^[1-9]\d{2}$ or ^[1-9]\d{3}$
4. Retain per 10-year retention policy

---

### 2.3 Bank Reconciliation Template

**File:** `docs/bank-cash/templates/bank-reconciliation-template.md`

```
# Bank Reconciliation Record

**Date:** {{DATE}} (DD/MM/YYYY)  
**Prepared by:** {{PREPARED_BY_NAME}} ({{ROLE}}, UUID: {{ACTOR_UUID}})  
**Company:** {{COMPANY_NAME}} (ID: {{COMPANY_UUID}})  
**Bank Account:** {{BANK_ACCOUNT_ID}} ({{BANK_NAME}} - {{ACCOUNT_NUMBER}})  
**Reconciliation Status:** {{STATUS}} (UNRESOLVED / RESOLVED / RESOLVED_WITH_DISCREPANCY)  

## 1. Balance Information

| Component | Amount (VND) | Notes |
|-----------|--------------|-------|
| **Statement Balance** (from bank statement) | {{STATEMENT_BALANCE}} | Per bank's official statement |
| **Internal Balance** (from company records) | {{INTERNAL_BALANCE}} | Per company's accounting records |
| **Difference** | {{DIFFERENCE}} = Statement - Internal | Auto-calculated: {{STATEMENT_BALANCE}} - {{INTERNAL_BALANCE}} |
| **Tolerance** | 0.01 VND | Reconciliation balanced if |difference| ≤ tolerance |

## 2. Reconciliation Details

**Reconciliation Period:** {{FROM_DATE}} to {{TO_DATE}}  
**Bank Statement Reference:** {{STATEMENT_REFERENCE}} (number/date from bank)  
**Internal Reference:** {{INTERNAL_REFERENCE}} (voucher/journal reference)  
**Outstanding Items:** {{OUTSTANDING_ITEMS}} (checks not yet cleared, deposits in transit)  

**Items reviewed and checked:**
- [ ] All transactions in statement match internal records
- [ ] No duplicate entries
- [ ] Correct posting dates
- [ ] Currency match (both VND)
- [ ] Opening balance carried forward correctly

## 3. SOD (Separation of Duties) Requirements

| Role | Action | Required | Reason |
|------|--------|----------|--------|
| **CHIEF_ACCOUNTANT** | Approve resolution (2nd actor) | Yes | Critical financial reconciliation requires 2-actor approval |
| **ACCOUNTANT** | Initiate reconciliation (1st actor) | Yes | Creates the reconciliation record |
| **AUDITOR** | Verify checksum integrity | Yes (read-only) | Audit trail compliance |

## 4. Resolution Outcomes

| Outcome | Condition | Checksum Events |
|---------|-----------|-----------------|
| **RESOLVED** | |difference| ≤ 0.01, 2nd actor approves | 2 checksums: 1st actor request + 2nd actor approval |
| **RESOLVED_WITH_DISCREPANCY** | |difference| > 0.01, 2nd actor forces resolution | 2 checksums with reason "FORCED_DISCREPANCY" |
| **UNRESOLVED** | 2nd actor rejects or difference unexplained | Remains UNRESOLVED, investigation flag raised, 2 checksums (request + reject) |

## 5. Audit & Retention

- **Checksum Algorithm:** SHA-256 chaining (prev + actor + now + action + reason + reconciliation_id)
- **Retention Period:** 10 years minimum per Luật Kế toán 2015, Article 11
- **Unresolved Older Than 365 Days:** Escalated to CHIEF_ACCOUNTANT via notification
- **Destruction:** Formal request required, Certificate of Destruction generated
- **Audit Events:** Created on: Reconciliation creation, 1st actor approval, 2nd actor approval/rejection

## 6. Sign-off

**Prepared by:** {{PREPARED_BY_SIGNATURE}} ({{ROLE}})

**1st Actor (ACCOUNTANT):** {{1ST_ACTOR_SIGNATURE}} (UUID: {{1ST_ACTOR_UUID}})

**2nd Actor (CHIEF_ACCOUNTANT):** {{2ND_ACTOR_SIGNATURE}} (UUID: {{2ND_ACTOR_UUID}})

**Date:** {{SIGNING_DATE}}

---

### Usage:
1. Copy this template to a new file
2. Replace all {{PLACEHOLDERS}} with actual values
3. reconcile difference automatically calculated: Statement Balance - Internal Balance
4. For RESOLVED: |difference| ≤ 0.01 VND
5. For RESOLVED_WITH_DISCREPANCY: difference noted with forced approval
6. Retain per 10-year retention policy

---

### 2.4 Bank Statement Import (CAMT) Template

**File:** `docs/bank-cash/templates/bank-statement-import-template.md`

```
# Bank Statement Import (CAMT.053/CAMT.054) Request

**Date:** {{DATE}} (DD/MM/YYYY)  
**Prepared by:** {{PREPARED_BY_NAME}} ({{ROLE}}, UUID: {{ACTOR_UUID}})  
**Company:** {{COMPANY_NAME}} (ID: {{COMPANY_UUID}})  
**File:** {{CAMT_FILE_NAME}} (CAMT.053 or CAMT.054, {{FILE_SIZE}} KB)  
**Import Status:** {{STATUS}} (PENDING / SUCCESS / FAILED)  

## 1. Import Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **File Format** | {{FILE_FORMAT}} | CAMT.053 or CAMT.054 (mandatory) |
| **Maximum File Size** | {{MAX_FILE_SIZE}} KB | Configurable, default 10MB |
| **Maximum Transactions** | {{MAX_TRANSACTIONS}} | Configurable, default 1000 per file |
| **Company ID** | {{COMPANY_UUID}} | Must match all transactions in file |
| **Currency** | {{CURRENCY_CODE}} | ISO 4217 format ^[A-Z]{3}$ (e.g., VND) |

## 2. File Contents Summary

| Total Rows | {{TOTAL_ROWS}} |
|------------|----------------|
| Valid Rows | {{VALID_ROWS}} |
| Invalid Rows | {{INVALID_ROWS}} |
| Imported Transactions | {{IMPORTED_COUNT}} |
| Failed Transactions | {{FAILED_COUNT}} (0 if all-or-nothing) |

**Row Details:**
| Row # | Date | Amount (VND) | Description | Status | Error Message (if invalid) |
|-------|------|--------------|-------------|--------|---------------------------|
| 1 | {{ROW1_DATE}} | {{ROW1_AMOUNT}} | {{ROW1_DESC}} | {{ROW1_STATUS}} | {{ROW1_ERROR}} |
| 2 | {{ROW2_DATE}} | {{ROW2_AMOUNT}} | {{ROW2_DESC}} | {{ROW2_STATUS}} | {{ROW2_ERROR}} |
| ... | ... | ... | ... | ... | ... |

## 3. Import Processing Rules

| Rule | Description | Enforced By |
|------|-------------|-------------|
| **All-or-Nothing** | If ANY row fails, entire import rolled back, NO data saved | Service layer, DB transaction |
| **Company Isolation** | All transactions must belong to same company_id | Service layer FK check |
| **Currency Validation** | All amounts in ISO 4217 code (^[A-Z]{3}$) | Entity validation |
| **Amount ≠ 0** | Zero-amount transactions rejected | Service layer validation |
| **Date Validity** | Transaction date must be valid, not future beyond 90 days | Service layer validation |

## 4. SOD (Separation of Duties) Requirements

| Role | Action | Required | Reason |
|------|--------|----------|--------|
| **CHIEF_ACCOUNTANT** | Authorize import (if threshold exceeded) | Yes (for > threshold) | Large imports require chief approval |
| **ACCOUNTANT** | Review imported transactions | Yes (per transaction) | Verify accuracy post-import |
| **AUDITOR** | Checksum verification | Yes (read-only) | Audit trail compliance |

## 5. Audit & Retention

- **Checksum Algorithm:** SHA-256 chaining per transaction event
- **Retention Period:** 10 years minimum per Luật Kế toán 2015, Article 11
- **Atomic Import:** All-or-nothing — no partial saves
- **Audit Events:** Created on: Import start, each valid row, import completion/failure
- **Destruction:** Formal request required, Certificate of Destruction generated

## 6. Sign-off

**Prepared by:** {{PREPARED_BY_SIGNATURE}} ({{ROLE}})

**Authorized by (CHIEF_ACCOUNTANT - if > threshold):** {{CHIEF_SIGNATURE}} (UUID: {{CHIEF_UUID}})

**Date:** {{SIGNING_DATE}}

---

### Usage:
1. Copy this template to a new file
2. Replace all {{PLACEHOLDERS}} with actual values
3. Upload CAMT.053 or CAMT.054 file via UI (POST /api/v1/reconciliations/import or dedicated import endpoint)
4. If any row fails: entire import rejected, no partial data
5. Retain per 10-year retention policy

---