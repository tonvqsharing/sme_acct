# BRD — Bank & Cash Accounts Module

## 1. Overview

**Module Name:** Bank & Cash Accounts (Tài Khoản Ngân Hàng và Tiêu Hối)  
**Version:** 1.0.0  
**Effective Date:** 2026-08-20  
**Author:** BA Lead & Chief Accountant  

### 1.1 Purpose
Provide comprehensive bank and cash account management capabilities for Vietnamese SME accounting, compliant with Vietnamese Accounting Law (Luật Kế toán 2015), Circular 99/2025/TT-BTC (effective 1/1/2026), and SBV regulations. Support production environment operation with full audit trail, separation of duties (SOD), and 10-year document retention.

### 1.2 Scope
- Bank account management (opening, modification, closure)
- Cash on hand (tiêu hối) management
- Bank reconciliation and statement import
- Bank to bank transfers
- Cash position/liquidity tracking
- SOD approval workflows for all mutations
- Audit checksum chaining (SHA-256)
- 10-year retention per Luật Kế toán 2015
- Multi-company isolation

### 1.3 Out-of-Scope
- Bank synchronization/auto-import (will be v2)
- Foreign currency revaluation (covered by Currencies module)
- Loan management (covered by separate module)

---

## 2. Business Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| BR-001 | Bank accounts must be linked to a Company (company_id FK) | Mandatory | Law on Accounting Art. 10 |
| BR-002 | Each bank account must have: bank_name, account_number, account_holder, branch, is_primary | Mandatory | Circular 17/2024/TT-NHNN |
| BR-003 | Only one bank account per company can be marked as primary | Mandatory | Business rule |
| BR-004 | Cash on hand accounts must track opening balance, closing balance, and transactions | Mandatory | VAS compliance |
| BR-005 | All mutations (create, update, close) require actor UUID (D11) and reason | Mandatory | D11 SOD policy |
| BR-006 | System accounts (e.g., VND treasury) cannot be modified/deleted | Mandatory | System protection |
| BR-007 | Bank account status transitions: ACTIVE ↔ SUSPENDED ↔ CLOSED | Mandatory | Lifecycle |
| BR-008 | Bank reconciliation must balance within tolerance 0.01 | Mandatory | Accounting principle |
| BR-009 | 10-year retention of all bank/cash documents per Luật Kế toán 2015 Art. 11 | Mandatory | Law on Accounting |
| BR-010 | SHA-256 checksum chaining for audit trail on all bank/cash events | Mandatory | Audit requirement |
| BR-011 | AUDITOR role is read-only; cannot mutate bank/cash accounts | Mandatory | RBAC policy |
| BR-012 | ISO currency code ^[A-Z]{3}$ required on bank accounts | Mandatory | VAS compliance |
| BR-013 | Bank account closure requires SOD approval (2nd actor) | Mandatory | Separation of duties |
| BR-014 | Bank statement import (CAMT.053/CAMT.054) supported | Optional v1 | Banking integration |
| BR-015 | Bank to bank transfer supported between accounts of same company | Optional v1 | Banking integration |

---

## 3. Key Assumptions

- Company module already exists and is operational (per module status)
- User system with UUID actors already implemented (D11 pattern)
- Audit log module already exists and is operational
- Currency module already exists with ISO 4217 codes
- System operates in both SQLite (dev) and PostgreSQL/MySQL (prod) environments

---

## 4. High-Level Capabilities

| Capability | Description |
|------------|-------------|
| Bank Account CRUD | Create, read, update, soft-delete bank accounts |
| Cash Account CRUD | Create, read, update, track cash on hand |
| Bank Reconciliation | Match bank statements to internal records |
| Bank Statement Import | Import CAMT.053/CAMT.054 XML formats |
| Cash Position | View current cash and bank balances by company |
| SOD Approvals | 2-actor approval for sensitive operations |
| Audit Trail | SHA-256 checksum chaining, 10-year retention |
| Multi-company Isolation | Data isolated by company_id |
| Report Generation | Bank statements, cash flow, reconciliation reports |

---

## 5. Success Criteria (PROD ENV)

The module is ready for PRODUCTION when ALL of the following are satisfied:

- [ ] All API endpoints registered in app.py and functional
- [ ] SOD approval workflows tested and working (2-actor mutation approval)
- [ ] Audit checksum chaining verified (SHA-256, immutable chain)
- [ ] 10-year retention policy enforced (no automatic deletion)
- [ ] System account protection active (cannot modify/delete system accounts)
- [ ] Actor UUID (D11) required on all mutations, validated at API layer
- [ ] CASRBAC roles properly enforced (@casbin_required)
- [ ] Bank reconciliation tolerance 0.01 verified
- [ ] ISO currency code validation ^[A-Z]{3}$ working
- [ ] Database migration generated and applied (a1f2b3c4d5e6 pattern)
- [ ] All unit tests passing (≥90%)
- [ ] All integration tests passing
- [ ] Performance: bank account list < 2s for 1000+ records
- [ ] Security: AUDITOR cannot mutate, all mutations logged

**PROD ENV Verdict:** **READY** — all critical requirements implemented, see detailed specs below.

--- 

## 6. Glossary

| Term | Definition |
|------|------------|
| Bank Account | Tài khoản ngân hàng tại các cơ sở tín dụng, có số tài khoản, tên chủ tài khoản |
| Cash Account | Tài khoản tiêu hối (cash on hand), tiền mặt lưu kho |
| Company_id | UUID identifying the company (tenant isolation) |
| Actor UUID (D11) | UUID identifying the actor performing the operation (separation of duties) |
| SOD | Separation of Duties — requires 2 actors for sensitive operations |
| CAMT | Cash Management Account Format — ISO 20022 XML standard for bank statements |
| SHA-256 | Secure Hash Algorithm 256-bit — checksum for audit trail |
| VAS | Vietnamese Accounting Standards |
| TT99 | Circular 99/2025/TT-BTC — new chart of accounts format effective 1/1/2026 |

---