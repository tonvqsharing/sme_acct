# Functional Specifications: Audit Log Configuration Module

## Overview
The Audit Log Configuration module provides immutable, tamper-proof audit trail functionality for the Vietnamese SME accounting application. It captures all critical business events and system changes with complete context for compliance with Vietnamese accounting law and international standards.

## 1. Module Architecture

### 1.1 Database Model: SystemAuditLog
```python
class SystemAuditLog(Base):
    __tablename__ = "audit_log"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(nullable=False, index=True)
    # Vietnamese chart of accounts regimes: TT200, TT99, TT58_MICRO, TT133
    entity_id: Mapped[int] = mapped_column(nullable=False, index=True)
    action: Mapped[str] = mapped_column(nullable=False, index=True)  # CREATE, UPDATE, DELETE, APPROVE, REJECT, SUSPEND, REACTIVATE, DISSOLVE
    field_name: Mapped[str] = mapped_column(nullable=True, index=True)  # NULL for whole-entity actions
    before_value: Mapped[str] = mapped_column(nullable=True)  # JSON string or NULL
    after_value: Mapped[str] = mapped_column(nullable=True)  # JSON string or NULL
    actor_id: Mapped[int] = mapped_column(nullable=False, index=True)  # User ID who performed action
    changed_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    
    # Composite index for performance
    __table_args__ = (
        Index('ix_audit_log_entity', 'entity_type', 'entity_id', 'changed_at'),
        Index('ix_audit_log_actor', 'actor_id', 'changed_at'),
    )
```

### 1.2 Immutability Enforcement
- **Database-Level**: Partial unique index + triggers to prevent UPDATE/DELETE on audit_log
- **Application-Level**: All write operations go through AuditLogService, direct DB access blocked
- **Storage**: Append-only design; records only ever inserted, never modified/deleted

### 1.3 Retention Policy
- **Minimum**: 10 years per Luật Kế toán 2015
- **Automatic Lifecycle**: 
  - Year 1-3: Hot storage (primary database, fast access)
  - Year 4-7: Warm storage (indexed, moderate cost)
  - Year 8-10: Cold storage (archived, slow access, low cost)
  - After year 10: Secure destruction with Certificate of Destruction
- **Scheduled Job**: Daily/weekly retention policy enforcement

## 2. Core Functional Requirements

### FR-1: Audit Record Creation
| Requirement | Detail |
|---|---|
| FR-1.1 | System must capture audit record on: CREATE, UPDATE, DELETE, APPROVE, REJECT, SUSPEND, REACTIVATE, DISSOLVE actions on: Company, Partner, Invoice, Voucher, BankAccount, Config entities |
| FR-1.2 | Each audit record must contain: entity_type, entity_id, action, field_name (NULL for whole-entity), before_value (JSON, NULL if not applicable), after_value (JSON, NULL if not applicable), actor_id, changed_at |
| FR-1.3 | actor_id must be valid, active user in the system |
| FR-1.4 | changed_at defaults to server timestamp on record creation |
| FR-1.5 | entity_type must be from validated enum: ['Company', 'Partner', 'Invoice', 'Voucher', 'BankAccount', 'Config'] |

### FR-2: Audit Record Retrieval
| Requirement | Detail |
|---|---|
| FR-2.1 | Auditor can filter by: entity_type, entity_id, action, field_name, date range, actor_id, before_value pattern, after_value pattern |
| FR-2.2 | Export formats: Excel (.xlsx), CSV, PDF (with digital signature) |
| FR-2.3 | Pagination support (page, page_size) |
| FR-2.4 | Search supports: exact match, LIKE pattern, date range, entity combination |
| FR-2.5 | Export includes: all fields, timestamps, user names (not just IDs) |

### FR-3: Integrity Verification
| Requirement | Detail |
|---|---|
| FR-3.1 | SHA-256 chaining: each record's hash includes previous record's hash + current record data |
| FR-3.2 | Root hash stored in immutable configuration table, verified on each access |
| FR-3.3 | Background job verifies chain integrity daily, alerts on discrepancy |
| FR-3.4 | Tamper detection: any UPDATE/DELETE attempt triggers immediate alert |
| FR-3.5 | Integrity report generated monthly for compliance auditors |

### FR-4: Retention Management
| Requirement | Detail |
|---|---|
| FR-4.1 | Automatic archival to cold storage after 3 years (configurable) |
| FR-4.2 | Secure deletion after 10 years with Certificate of Destruction |
| FR-4.2.1 | Certificate includes: record count, hash of deleted records, destruction date, authorized person |
| FR-4.3 | Retention policy configurable per entity_type (default 10 years for all) |
| FR-4.4 | Minimum retention cannot be reduced below 10 years without compliance approval |

### FR-5: Separation of Duties (SoD)
| Requirement | Detail |
|---|---|
| FR-5.1 | System Administrator (SA) cannot UPDATE/DELETE audit_log records |
| FR-5.2 | Audit Administrator (AA) has READ-only access to audit_log |
| FR-5.3 | AA can: export, verify integrity, view all records; CANNOT modify |
| FR-5.4 | SA manages users, configs, periods; CANNOT access audit_log content |
| FR-5.5 | SoD enforced at database level (different roles/permissions) |

### FR-6: User Context Capture
| Requirement | Detail |
|---|---|
| FR-6.1 | Every audit record captures: user full name, user role, user ID |
| FR-6.2 | IP address of client session recorded |
| FR-6.3 | User agent (browser/APP version) recorded |
| FR-6.4 | Session ID recorded for traceability |
| FR-6.5 | Authentication token type recorded (Bearer, Session, 2FA-verified) |

## 3. Non-Functional Requirements

### NFR-1: Immutability
- **Critical**: No mechanism exists to modify or delete audit_log records via application API
- **Database trigger**: Prevents any UPDATE/DELETE on audit_log table
- **Role restriction**: DB roles grant INSERT only on audit_log for application user

### NFR-2: Performance
- **Query latency**: < 500ms for filtered searches on last 3 years
- **Index strategy**: Composite indexes on (entity_type, entity_id, changed_at), (actor_id, changed_at)
- **Batch insert**: Audit records written in transaction with source entity write

### NFR-3: Storage Efficiency
- **before_value/after_value**: Stored as compact JSON; large fields serialized to separate table if > KB
- **Retention-based migration**: Automatic migration to archive storage per policy
- **Retention**: 10-year minimum, beyond configurable per entity_type

### NFR-4: Audit Integrity
- **Checksum verification**: Daily background job, < 5min for 1M records
- **Alert threshold**: Any discrepancy triggers immediate PagerDuty/Slack alert
- **Tamper-evidence**: SHA-256 chain; any break identified within 1 minute

### NFR-5: Compliance
- **Vietnamese law**: Luật Kế toán 2015 (10-year), Nghị định 123/2020/NĐ-CP (e-invoice history)
- **International**: ISO 27001, SOC 2, IFRS S2
- **Audit readiness**: System produces compliant audit report on demand

## 4. API Endpoints (Presentation Layer)

### POST /api/audit/log
- **Request**: {entity_type, entity_id, action, field_name?, before_value?, after_value?, actor_id}
- **Response**: {id, entity_type, action, changed_at}
- **Auth**: Requires authentication, authorization check per SoD rules

### GET /api/audit/log
- **Query params**: entity_type, entity_id, action, field_name, start_date, end_date, actor_id, page, page_size
- **Response**: Paged audit records with filters applied

### GET /api/audit/log/export
- **Query params**: Same as GET + format (xlsx, csv, pdf)
- **Response**: File download with audit report

### POST /api/audit/integrity/verify
- **Request**: {}
- **Response**: {valid, root_hash, checked_records, discrepancy?, verified_at}
- **Auth**: Audit Administrator only

### GET /api/audit/retention/status
- **Response**: {current_retention_years, next_archival, next_deletion, compliance_status}

## 5. Integration Points

### 5.1 With Company Module
- Audit log on Company CREATE/UPDATE/SUSPEND/REACTIVATE/DISSOLVE
- entity_type = 'Company', entity_id = company.primary_key

### 5.2 With Partner Module
- Audit log on Partner CREATE/UPDATE/tax_id change
- entity_type = 'Partner', entity_id = partner.primary_key

### 5.3 With Invoice Module
- Audit log on Invoice CREATE/UPDATE/VOID/SUSPEND/REACTIVATE
- entity_type = 'Invoice', entity_id = invoice.primary_key

### 5.4 With Voucher Module
- Audit log on Voucher POST/DRAFT/POSTED/CANCELLED
- entity_type = 'Voucher', entity_id = voucher.primary_key

### 5.5 With BankAccount Module
- Audit log on BankAccount CREATE/UPDATE/SET_DEFAULT/DELETE
- entity_type = 'BankAccount', entity_id = bank_account.primary_key

### 5.6 With System Settings
- Audit log on Config update, period lock/unlock, VAT rate validation
- entity_type = 'Config', entity_id = config.primary_key

## 6. Data Fllow Diagrams

### 6.1 Audit Record Creation Flow
```
User Action
    │
    ▼
Authorization Check (SoD: user has 'audit:write' permission?)
    │
    ├─── Yes ───────────────────────────────────► AuditLogService.create()
    │                                       │
    │                                       ▼
    │                                Transaction:
    │                                1. Write source entity change
    │                                2. Write audit_log record (INSERT only)
    │                                3. Commit both or rollback both
    │                                       │
    │                                       ▼
    │                               Audit record immutable in DB
    │                                       │
    └─── No ──────────────────────────────────────► 403 Forbidden
                                            (SoD violation)
    │
    ▼
Alert: SoD violation attempt logged to separate security audit trail

### 6.2 Audit Record Retrieval Flow
```
Auditor Request
    │
    ▼
Authorization Check (SoD: user has 'audit:read' permission?)
    │
    ├─── Yes ───────────────────────────────────► Query audit_log with filters
    │                                       │
    │                                       ▼
    │                               Return paged results
    │                                       │
    └─── No ──────────────────────────────────────► 403 Forbidden
    │
    ▼
Alert: Unauthorized audit access attempt

### 6.3 Integrity Verification Flow
```
Audit Admin Initiation
    │
    ▼
Background Job: verify_audit_chain()
    │
    ├──► Step 1: Read first record, compute SHA-256
    │       │
    │       ▼
    │       Step 2: Read second record, compute:
    │       │       expected_hash = SHA256(prev_hash + current_data)
    │       │       if expected_hash != current_hash: flag discrepancy
    │       │
    │       ▼
    │       Step 3: Repeat for all records to end
    │
    │
    ▼
Generate integrity report:
    • valid: true/false
    • root_hash: SHA-256 of first record
    • checked_records: total count
    • discrepancy: location/type if any
    • verified_at: timestamp
    │
    ▼
Alert if discrepancy found → PagerDuty/Slack → AA investigation

### 6.4 Retention Lifecycle Flow
```
Day 0: Record created
    │
    ├──► Year 1-3: Hot storage (primary DB, fast)
    │       │
    │       ├──► Daily: Backup includes audit_log
    │       ├──► Weekly: Performance optimization
    │       └──► On-demand: Quick search/export
    │
    ├──► Year 4-7: Warm storage (read-only replica, indexed)
    │       │
    │       ├──► Monthly: Archive backup
    │       ├──► Quarterly: Integrity verification
    │       └──► On-demand: Search slower (hours vs minutes)
    │
    ├──► Year 8-10: Cold storage (separate storage, low cost)
    │       │
    │       ├──► Annual: Migration from warm to cold
    │       ├──► Annual: Compliance review
    │       └──► On-demand: Export requires restoration (24h)
    │
    └──► After Year 10: Secure destruction
            │
            ├──► Generate Certificate of Destruction
            ├──► Execute DELETE with audit trail
            ├──► Secure overwrite (Gutmann method)
            └──► Log destruction in separate immutable record
```

## 7. User Journeys

### 7.1 Auditor Journey: Export Audit Report
1. Login to system with Auditor role
2. Navigate to Audit Log module
3. Filter by: date range (last fiscal year), entity_type (Invoice), action (CREATE, UPDATE)
4. Click "Export"
5. Select format: Excel (.xlsx)
6. System generates file with:
   - All audit records matching criteria
   - Column headers: Date, Entity Type, Entity ID, Action, Field Changed, Before Value, After Value, User, IP, Timestamp
   - Summary section: record count, date range, filter criteria
7. Download file, verify completeness
8. Submit to external auditors

### 7.2 System Admin Journey: Configure Retention
1. Login with System Administrator role
2. Navigate to System Settings → Retention Policy
3. View current policy: 10 years minimum (non-changeable)
4. Configure entity-specific retention (if needed):
   - Company: 10 years (default, immutable)
   - Invoice: 10 years (default, immutable)
   - Voucher: 10 years (default, immutable)
   - (Cannot reduce below 10 years without compliance approval)
5. Save configuration
6. System schedules automatic archival/deletion jobs
7. Confirmation: "Retention policy updated. Next archival in 3 years."

### 7.3 Compliance Officer Journey: Verify Integrity
1. Login with Compliance Officer role
2. Navigate to Audit Log → Integrity Verification
3. Click "Verify Chain"
4. System runs background job (takes proportionate to record count)
5. Results displayed:
   - Chain valid: ✓
   - Root hash: abc123def456...
   - Records checked: 2,847,519
   - Discrepancies: 0
   - Verified at: 2026-01-15 14:30:00
6. Download integrity report
7. Report to board: audit trail integrity confirmed

### 7.4 IT Security Manager Journey: Investigate Suspicious Activity
1. Login with IT Security Manager role
2. Navigate to Audit Log → Search
3. Filter by: unusual time (23:00-05:00), unknown actor_id, specific entity (Company)
4. Review audit records:
   - User accessed Company record at 02:15 AM
   - Action: UPDATE
   - Field: status changed from ACTIVE to SUSPENDED
   - Before: "ACTIVE"
   - After: "SUSPENDED"
   - User ID: 45 (service account)
   - IP: 203.105.12.78 (external subnet)
   - User agent: Custom script (suspicious)
5. If SoD violation: generate alert, notify Compliance Officer
6. If normal operation: document, close case

## 8. Business Rules (Hard-Coded)

### BR-1: Immutable Audit Trail
- **Rule**: Once an audit record is INSERTed, it MUST never be UPDATE or DELETE via application API
- **Enforcement**: Database trigger prevents any UPDATE/DELETE on audit_log table
- **Exception**: None - zero exceptions for core audit table

### BR-2: Minimum Retention
- **Rule**: All audit records retained minimum 10 years per Luật Kế toán 2015
- **Enforcement**: Retention policy engine; cannot be configured below 10 years
- **Exception**: Compliance approval required to reduce; rare, documented, signed

### BR-3: Complete Field Capture
- **Rule**: Every audit record must have: entity_type, entity_id, action, actor_id, changed_at
- **before_value**: Required if action = UPDATE and field_name is specified
- **after_value**: Required if action = UPDATE and field_name is specified
- **Relaxation**: CREATE action may have NULL before_value; DELETE action may have NULL after_value

### BR-4: Actor Validation
- **Rule**: actor_id must reference an active, authenticated user in the system
- **Enforcement**: Pre-insert validation; reject audit record if actor_id inactive/blocked
- **Service accounts**: Allowed with prefix "SA-" and additional validation

### BR5: Action Enum (Closed)
- **Rule**: action must be from closed enum: CREATE, UPDATE, DELETE, APPROVE, REJECT, SUSPEND, REACTIVATE, DISSOLVE
- **Enforcement**: Application-level check; reject unknown action values
- **Extension**: New actions require migration and release notes

### BR6: Entity Type Enum (Closed)
- **Rule**: entity_type must be from closed enum: Company, Partner, Invoice, Voucher, BankAccount, Config
- **Enforcement**: Application-level check; reject unknown entity types
- **Extension**: New entity types require domain model update

### BR7: SoD Enforcement
- **Rule**: System Administrator role cannot have 'audit:read' or 'audit:write' permission
- **Enforcement**: DB role separation; application code checks role + permission combination
- **Violation**: Immediate alert, security incident classification

### BR8: Hash Chain Integrity
- **Rule**: SHA-256 chain must be valid for all records; any break triggers immediate alert
- **Enforcement**: Daily background job; root hash stored in immutable config
- **Recovery**: If chain broken, must restore from last known good backup + re-verify

### BR9: IP Address Capture
- **Rule**: Client IP address must be captured for every audit record
- **Enforcement**: AuditLogService receives IP from request context; stored in actor_ip field
- **Exception**: Localhost/internal processes may have NULL IP (documented)

### BR10: User Agent Capture
- **Rule**: User agent string captured for every audit record
- **Enforcement**: AuditLogService receives user-agent from HTTP request headers
- **Format**: Free text, stored as-is

## 9. Templates

### 9.1 Audit Log Entry Template (JSON)
```json
{
  "id": 123456,
  "entity_type": "Invoice",
  "entity_id": 987654,
  "action": "UPDATE",
  "field_name": "vat_rate",
  "before_value": "0.10",
  "after_value": "0.15",
  "actor_id": 42,
  "actor_name": "Nguyen Van A",
  "actor_role": "Accountant",
  "changed_at": "2026-01-15T14:30:00+07:00",
  "actor_ip": "10.10.10.10",
  "actor_user_agent": "Mozilla/5.0 Chrome/120.0"
}
```

### 9.2 Integrity Verification Report Template
```markdown
# Audit Log Integrity Verification Report

**Report ID**: INTEGRITY-20260115-001
**Generated**: 2026-01-15 14:30:00 UTC
**Verifier**: Compliance Officer (role: compliance_officer)

## Chain Validation
- **Valid**: ✓ YES
- **Root Hash**: `a1b2c3d4e5f6...` (SHA-256 of first record)
- **Total Records Checked**: 2,847,519
- **Discrepancies Found**: 0
- **First Record ID**: 1
- **Last Record ID**: 2847519

## Storage Status
- **Hot Storage (0-3 years)**: 842,115 records
- **Warm Storage (4-7 years)**: 1,123,402 records
- **Cold Storage (8-10 years)**: 882,002 records
- **Beyond Retention**: 0 records (all within 10-year policy)

## Compliance Status
- **Vietnamese Law (Luật Kế toán 2015)**: ✓ COMPLIANT (10-year minimum retention)
- **E-invoice History (Nghị định 123/2020/NĐ-CP)**: ✓ COMPLIANT
- **Data Protection (Nghị định 13/2023/NĐ-CP)**: ✓ COMPLIANT
- **ISO 27001**: ✓ COMPLIANT
- **SOC 2**: ✓ COMPLIANT

## Action Items
- [ ] No action required - chain valid
- [ ] Review discrepancies (if any): 0 found
- [ ] Next verification: 2026-02-15
```

### 9.3 Retention Policy Configuration Template
```markdown
# Audit Log Retention Policy Configuration

**Configuration ID**: RETENTION-20260115-001
**Last Updated**: 2026-01-15 10:00:00 UTC
**Updated By**: System Administrator (role: sysadmin)

## Policy Settings
- **Minimum Retention Years**: 10 (immutable, per Luật Kế toán 2015)
- **Default Entity Retention**: 10 years (all entity types)
- **Archival Threshold**: 3 years (move from hot to warm storage)
- **Deletion Threshold**: 10 years (after secure destruction)

## Entity-Specific Retention (Read-Only)
| Entity Type | Retention Years | Changeable | Last Changed |
|-------------|----------------|------------|--------------|
| Company | 10 | ❌ NO (immutable) | N/A |
| Partner | 10 | ❌ NO (immutable) | N/A |
| Invoice | 10 | ❌ NO (immutable) | N/A |
| Voucher | 10 | ❌ NO (immutable) | N/A |
| BankAccount | 10 | ❌ NO (immutable) | N/A |
| Config | 10 | ❌ NO (immutable) | N/A |

## Change Log
| Date | Changed By | Change | Reason |
|------|------------|--------|--------|
| N/A | N/A | No changes permitted | Minimum 10 years mandated by law |

## Next Scheduled Actions
- **Archival Job**: 2026-04-15 (move 3-year-old records to warm storage)
- **Integrity Verification**: 2026-02-15 (daily chain check)
- **Compliance Review**: 2026-10-15 (annual review, next possible change date)

## Approvals
- **Required**: Compliance Officer approval to reduce retention below 10 years
- **Current**: No reduction permitted (minimum 10 years enforced)
```

### 9.4 SoD Role Assignment Template
```markdown
# Separation of Duties (SoD) Role Assignment

**Configuration ID**: SOD-20260115-001
**Effective**: 2026-01-15
**Authorized By**: Compliance Officer + IT Security Manager

## Roles and Permissions

### System Administrator (SA)
- **DB Roles**: 
  - `company_rw`: CRUD on company data
  - `invoice_rw`: CRUD on invoice data
  - `user_mgmt`: User creation/management
  - `config_rw`: System configuration changes
- **Application Permissions**:
  - `system:configure`: Configure system params
  - `period:lock_unlock`: Lock/unlock accounting periods
  - `audit:VIEW`: ❌ DENIED (SoD violation)
  - `audit:EXPORT`: ❌ DENIED (SoD violation)
- **SoD Principle**: SA manages operations, AA manages audit

### Audit Administrator (AA)
- **DB Roles**:
  - `audit_r`: READ-only on audit_log table
  - `config_r`: READ on system config (no WRITE)
- **Application Permissions**:
  - `audit:READ`: ✓ ALLOWED (view all audit records)
  - `audit:EXPORT`: ✓ ALLOWED (export audit reports)
  - `audit:VERIFY`: ✓ ALLOWED (run integrity verification)
  - `audit:WRITE`: ❌ DENIED (SoD violation)
  - `system:configure`: ❌ DENIED (SoD violation)
- **SoD Principle**: AA monitors and verifies, SA operates the system

### Cross-Role Checks
| Check | SA Allowed | AA Allowed | Violation |
|-------|-----------|-----------|-----------|
| View audit log contents | ❌ No | ✓ Yes | SoD |
| Modify audit record | ❌ No | ❌ No | Immutable |
| Delete audit record | ❌ No | ❌ No | Immutable |
| Export audit report | ❌ No | ✓ Yes | - |
| Run integrity verification | ❌ No | ✓ Yes | - |
| Configure retention policy | ✓ Yes (but min 10y) | ❌ No | - |
| Lock period | ✓ Yes | ❌ No | - |
| Create user | ✓ Yes | ❌ No | - |

## Violation Detection and Alerts
- **Monitoring**: Real-time SoD violation detection
- **Alert Channel**: PagerDuty + Slack #security-alerts
- **Alert Content**: "SoD violation: [role] attempted [action] on [resource]"
- **Response**: Immediate investigation, documented incident, potential access review
- **Escalation**: Compliance Officer notified within 24 hours
```

## 10. Implementation Plan

### Phase 1: Database Enhancements (Sprint 1)
- [ ] Add actor_ip column to SystemAuditLog
- [ ] Add actor_user_agent column to SystemAuditLog
- [ ] Create database triggers for immutability (PREVENT UPDATE/DELETE)
- [ ] Create composite indexes for performance
- [ ] Migration script: Add columns, add triggers

### Phase 2: Service Layer (Sprint 2)
- [ ] AuditLogService with create() method
- [ ] Validation: entity_type enum, action enum, actor_id validation
- [ ] IP address capture from request context
- [ ] User agent capture from request headers
- [ ] before_value/after_value JSON formatting

### Phase 3: Repository Port (Sprint 2)
- [ ] Update SystemSettingsRepositoryPort.add_audit_log() signature
- [ ] Add audit_log query methods with filtering
- [ ] Add retention policy methods
- [ ] Add integrity verification methods

### Phase 4: API Endpoints (Sprint 3)
- [ ] POST /api/audit/log - create audit record
- [ ] GET /api/audit/log - query with filters
- [ ] GET /api/audit/log/export - export formats
- [ ] POST /api/audit/integrity/verify - integrity check (AA only)
- [ ] GET /api/audit/retention/status - retention status

### Phase 5: SoD and Permissions (Sprint 3)
- [ ] Database roles: audit_r (READ-only on audit_log)
- [ ] Application: role + permission checks for SoD
- [ ] Alerting: SoD violation detection and notification
- [ ] UI: role-based hiding of audit features

### Phase 6: Retention Management (Sprint 4)
- [ ] Automatic archival job (3-year threshold)
- [ ] Secure deletion job (10-year threshold)
- [ ] Certificate of Destruction generation
- [ ] Retention policy configuration UI

### Phase 7: Testing (Sprint 4-5)
- [ ] Unit tests for AuditLogService (all methods)
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for audit record creation + retrieval
- [ ] Integrity verification tests
- [ ] SoD violation tests
- [ ] Retention policy tests

### Phase 8: Documentation (Sprint 5)
- [ ] BRD (already completed)
- [ ] Functional specifications (completed)
- [ ] User manual for auditors
- [ ] Admin guide for retention configuration
- [ ] ADRs for key design decisions

### Phase 9: PROD Deployment (Sprint 5-6)
- [ ] Staging environment deployment
- [ ] Load testing for audit record creation performance
- [ ] Security penetration testing (focus on immutability)
- [ ] Compliance validation (Vietnamese law, ISO 27001)
- [ ] PROD environment deployment with rollback plan

## 11. Glossary

| Term | Definition |
|------|------------|
| **Audit Log** | Immutable record of all system changes with full context (who, what, when) |
| **WORM** | Write-Once-Read-Many: storage design where records can only be written, never modified/deleted |
| **SoD** | Separation of Duties: security principle dividing responsibilities between roles |
| **Retention Policy** | Rules governing how long data is kept before archival or destruction |
| **Checksum/Hash** | Cryptographic fingerprint; SHA-256 used for audit chain integrity |
| **Root Hash** | SHA-256 of the first audit record; stored immutably, verifies entire chain |
| **Cold/Warm/Hot Storage** | Tiered storage: cold=archived/low cost, warm=indexed/moderate, hot=primary/fast |
| **Certificate of Destruction** | Documented proof of secure data destruction with hash verification |
| **Tamper-Proof** | Mechanism preventing unauthorized modification of audit records |
| **ALCOA+** | Data integrity principles: Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, Available |

## 12. Success Criteria Checklist (PROD READY)

- [ ] Database triggers prevent ALL UPDATE/DELETE on audit_log table
- [ ] AuditLogService.create() validates all required fields before INSERT
- [ ] actor_id must reference active, authenticated user
- [ ] entity_type from closed enum: Company, Partner, Invoice, Voucher, BankAccount, Config
- [ ] action from closed enum: CREATE, UPDATE, DELETE, APPROVE, REJECT, SUSPEND, REACTIVATE, DISSOLVE
- [ ] SHA-256 chaining implemented and verified daily
- [ ] Retention policy: minimum 10 years per Vietnamese law
- [ ] Automatic archival at 3-year threshold
- [ ] Secure deletion at 10-year threshold with Certificate of Destruction
- [ ] SoD: SA cannot read/export audit logs; AA cannot configure system
- [ ] API endpoints: POST/GET/EXPORT/INTEGRITY VERIFY all functional
- [ ] Export produces complete records with all fields + user names
- [ ] Integrity verification report generates correctly
- [ ] Query performance: < 500ms for filtered search on last 3 years
- [ ] IP address captured for every audit record
- [ ] User agent captured for every audit record
- [ ] No hardcoded secrets or credentials in audit-related code
- [ ] All unit tests pass (100% for audit module)
- [ ] All integration tests pass
- [ ] Compliance validation: Vietnamese law (Luật Kế toán 2015, Nghị định 123/2020/NĐ-CP, Nghị định 13/2023/NĐ-CP)
- [ ] PROD deployment with monitoring and alerting

---