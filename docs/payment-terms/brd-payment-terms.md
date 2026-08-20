# BRD — Payment Terms & Document Numbering Module

## 1. Overview

**Module Name:** Payment Terms & Document Numbering (Kỷ hạn thanh toán & Số hiệu tài liệu)  
**Version:** 1.0.0  
**Effective Date:** 2026-08-20  
**Author:** BA Lead & Chief Accountant  

### 1.1 Purpose
Provide comprehensive Payment Terms management and Document Numbering capabilities for Vietnamese SME accounting, compliant with Vietnamese Accounting Law (Luật Kế toán 2015), Circular 99/2025/TT-BTC (effective 1/1/2026), and GDT regulations. Support production environment operation with full audit trail, 10-year document retention, and integration with Invoice module.

### 1.2 Scope
- Payment Terms (kiể hạn thanh toán) management (create, update, activate, deactivate)
- Document Numbering (số hiệu tài liệu) for invoices/Receipts/Vouchers
- Series prefix management (existing e-invoice series extension)
- Numbering sequence automation (atomic all-or-nothing)
- 10-year retention per Luật Kế toán 2015 Art. 11
- Integration with Invoice module (apply payment terms on invoice creation)
- CASRBAC enforcement (AUDITOR read-only)

### 1.3 Out-of-Scope
- Bank synchronization/auto-import (covered by Bank & Cash module)
- Customs declaration numbering (covered by separate module)

### 1.4 Glossary

| Term | Definition |
|------|------------|
| Payment Terms | Kể hạn thanh toán - agreed timeframes for payment (e.g., Net 30, Net 60) |
| Document Numbering | Số hiệu tài liệu - sequential numbering for accounting documents |
| Series Prefix | Chỉ sốserie - prefix format for document numbers (e.g., "HD-2026/") |
| Next Sequence | Số tiếp theo - auto-incremented number for each new document |
| E-Invoice Series | Bộ số hóa đơn điện tử - regulated series for electronic invoices per GDT Circular 163/2020/TT-BTC |

---

## 2. Business Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| BR-001 | Payment Terms must be linked to a Company (company_id FK) | Mandatory | Law on Accounting Art. 10 |
| BR-002 | Payment Terms must have: name, description, due_days, interest_rate | Mandatory | VAS compliance |
| BR-003 | Only one Payment Terms can be set as default per company | Mandatory | Business rule |
| BR-004 | Document Numbering series must have: prefix, next_sequence, is_active | Mandatory | GDT Circular 163/2020/TT-BTC |
| BR-005 | Maximum 15 active document numbering series per company | Mandatory | GDT regulation |
| BR-006 | Series prefix format must comply with GDT requirements | Mandatory | GDT Circular 163/2020/TT-BTC Art. 10 |
| BR-007 | All mutations (create, update, deactivate) require actor UUID (D11) and reason | Mandatory | D11 SOD policy |
| BR-008 | AUDITOR role is read-only; cannot mutate payment terms/document numbering | Mandatory | RBAC policy |
| BR-009 | 10-year retention of all numbering configurations per Luật Kế toán 2015 Art. 11 | Mandatory | Law on Accounting |
| BR-010 | SHA-256 checksum chaining for audit trail on all payment term events | Mandatory | Audit requirement |
| BR-011 | Document numbering series atomic: all-or-nothing (any failure → no partial save) | Mandatory | Data integrity |
| BR-012 | When creating invoice, apply payment terms due date calculation | Optional v1 | Invoice integration |
| BR-012 | Payment Terms due date = issue_date + due_days (business days) | Optional v1 | Invoice integration |

---

## 3. Key Assumptions

- Company module already exists and is operational (per module status)
- Invoice module already exists with payment_method field
- User system with UUID actors already implemented (D11 pattern)
- Audit log module already exists and is operational
- E-invoice series module partially exists (needs extension)
- System operates in both SQLite (dev) and PostgreSQL/MySQL (prod) environments

---

## 4. High-Level Capabilities

| Capability | Description |
|------------|-------------|
| Payment Terms CRUD | Create, read, update, soft-deactivate payment terms |
| Default Payment Terms | Set one payment terms as default per company |
| Due Date Calculation | Calculate invoice due date = issue_date + due_days |
| Document Numbering Series | Create, read, update, activate/deactivate numbering series |
| Series Prefix Validation | Validate prefix format per GDT requirements |
| Sequence Automation | Auto-increment next_sequence on each document creation |
| Audit Trail | SHA-256 checksum chaining, 10-year retention |
| Multi-company Isolation | Data isolated by company_id |

---

## 5. Success Criteria (PROD ENV)

The module is ready for PRODUCTION when ALL of the following are satisfied:

- [ ] All API endpoints registered in app.py and functional
- [ ] SOD approval workflows tested and working (actor UUID D11 validation)
- [ ] Audit checksum chaining verified (SHA-256, immutable chain)
- [ ] 10-year retention policy enforced (no automatic deletion)
- [ ] Series prefix format validated per GDT Circular 163/2020/TT-BTC
- [ ] Maximum 15 active series constraint enforced per company
- [ ] Actor UUID (D11) required on all mutations, validated at API layer
- [ ] CASRBAC roles properly enforced (@casbin_required)
- [ ] Database migration generated and applied
- [ ] All unit tests passing (≥90%)
- [ ] All integration tests passing
- [ ] Performance: list series < 2s for 100+ records
- [ ] Security: AUDITOR cannot mutate, all mutations logged

**PROD ENV Verdict:** **PENDING** — document numbering partially exists, payment terms need implementation. See detailed specs below.

---

## 6. Dependencies on Existing Modules

| Dependency | Status | Description |
|------------|--------|-------------|
| `Invoice` | Already exists | Invoice has payment_method field; needs payment_terms_id FK addition |
| `EInvoiceSeries` | Partial exists | Document numbering series already implemented in system_settings (max 15 active, prefix + next_sequence); needs extension for full document numbering |
| `Company` | Already exists | Payment terms/series belong to a company (company_id FK) |
| `AuditLogService` | Required | All events logged via audit_log_service.append_event() |
| `CASRBAC` | Required | @casbin_required decorator on all API routes |
| `SQLAlchemyRepository` | Required | DB adapters for PaymentTerm, DocumentNumberingSeries |

---

## 7. Glossary (Vietnamese-English)

| Vietnamese | English | Description |
|------------|---------|-------------|
| Kể hạn thanh toán | Payment Terms | Thời gian trả nợ thỏa thuận giữa buyer và seller (Ví dụ: Net 30, Net 60, Thanh toán sau 15 ngày) |
| Số hiệu tài liệu | Document Numbering | Mã dạng số để định danh các tài liệu kế toán (Hóa đơn, Phiếu thu, Phiếu chi) |
| Kỳ hạn | Due Date | Ngày tài phải thanh toán |
| Mã bộ số | Series Prefix | Chỉ số đầu tiên của số hiệu tài liệu (VD: "HD/" cho hóa đơn) |
| Số tiếp theo | Next Sequence | Số tự động tăng cho tài liệu mới |
| Bộ số hóa đơn điện tử | E-Invoice Series | Bộ số được GDT cấp cho hóa đơn điện tử |

---