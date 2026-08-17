# BRD: Audit Log Configuration Module

## Objective
Implement a complete Audit Log Configuration module for the Vietnamese SME accounting application that satisfies:
- **Vietnamese legal requirements**: Luật Kế toán 2015 (10-year retention), Nghị định 123/2020/NĐ-CP (e-invoice history), Nghị định 13/2023/NĐ-CP (data personal protection)
- **International standards**: ISO 27001 (information asset change recording), SOC 2 (change/origin tracking), IFRS S2 (sustainability data transparency)
- **Production readiness**: Immutable audit trail, tamper-proof, complete capture, verifiable integrity

## Target Users
- CFO / Finance Director (overall audit trail oversight)
- System Administrator (system configuration, user management)
- Auditor (external/internal audit examination)
- Compliance Officer (regulatory compliance monitoring)
- IT Security Manager (security incident investigation)

## Business Context
The Vietnamese SME accounting application must maintain complete, immutable audit trails for all financial transactions and system changes to satisfy:
1. **Mandatory legal requirement**: Luật Kế toán 2015 Article 11 - accounting books and documents retained minimum 10 years
2. **E-invoice compliance**: Nghị định 123/2020/NĐ-CP - electronic invoices must preserve original format and transmission history
3. **Data protection**: Nghị định 13/2023/NĐ-CP - balance transparency with personal data protection
4. **International business**: ISO 27001, SOC 2, IFRS S2 compliance for export-oriented companies

## Key Design Principles
- **Immutability**: Audit records cannot be modified or deleted once written (WORM principle)
- **Completeness**: Every critical change must be captured with full context (who, what, when, why)
- **Verifiability**: Integrity can be independently verified (checksums, chain validation)
- **Retention**: Automatic lifecycle management per Vietnamese law (10-year minimum)
- **Accessibility**: Auditable data must be searchable and exportable for auditors
- **SoD**: Separation of duties between system administration and audit administration

## Regulatory References (All Contextuated)
| Law/Decree | Status | Key Requirement |
|------------|--------|-----------------|
| Luật Kế toán 2015 (88/2015/QH13) | Current (effective 01/01/2017) | 10-year minimum retention for accounting books/docs |
| Thông tư 200/2014/TT-BTC | Legacy (replaced 01/01/2026) | Previous chart of accounts, voucher formats |
| Thông tư 99/2025/TT-BTC | Current (effective 01/01/2026) | New chart of accounts, TT200/TT99/TT58_MICRO/TT133 regimes |
| Nghị định 123/2020/NĐ-CP | Current | E-invoice decree, must preserve original format and history |
| Nghị định 13/2023/NĐ-CP | Current | Personal data protection, balance with transparency |

## Success Criteria (PROD ENV READY)
- [ ] Audit records are immutable (no UPDATE/DELETE on core audit table)
- [ ] All critical business events are captured with complete fields
- [ ] Retention policy enforces minimum 10-year storage per Vietnamese law
- [ ] Integrity verification (checksum chain) runs without errors
- [ ] Export functionality produces complete, accurate audit reports
- [ ] SoD enforcement: admin cannot modify/delete audit logs
- [ ] System operates in PROD ENV with all above criteria satisfied

## Current State Assessment
**Status**: PARTIALLY IMPLEMENTED - requires enhancements for PROD ENV deployment

**Existing**:
- audit_log table with 8 fields: id, entity_type, entity_id, action, field_name, before_value, after_value, actor_id, changed_at
- SystemSettingsService with lock_period/unlock_period methods
- Repository port with audit_log method
- Period lock functionality

**Missing for PROD ENV**:
- Immutability enforcement (WORM)
- Tamper-proof mechanism (SHA-256 chaining)
- Retention policy automation (10-year minimum)
- Audit log export functionality
- Separation of duties (SoD)
- Integrity verification system
- Digital signature capability

---