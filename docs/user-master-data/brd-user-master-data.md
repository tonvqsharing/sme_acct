# BRD: User Master Data Module (User Management)

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Status | DRAFT |
| Owner | BA Lead + Chief Accountant |
| Date | 2026-08-18 |
| Audience | Vietnamese SME accounting system — user/role management |

---

## 1. Executive Summary

**User Master Data** is the foundation for RBAC and audit traceability in the Vietnamese SME accounting system. Every operator (accountant, auditor, admin) must be registered in the system with a valid role. **No API endpoint, financial transaction, or system configuration change should proceed without an authenticated, authorized user context.**

Current codebase: **AuthService manages users via raw SQL `users` table** (not SQLAlchemy model). Roles: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR. pycasbin fallback active. **Production verdict: OPERATIONAL via fallback, but user management lacks full RBAC fine-grain control.**

---

## 2. Business Context

### 2.1 Target Users

| Persona | Role | Pain Point |
|---------|------|-----------|
| **Giám đốc / Chủ doanh nghiệp** | DIRECTOR | Needs full system oversight; user creation/role assignment |
| **Kế toán trưởng** | CHIEF_ACCOUNTANT | Needs company financial oversight; can suspend/reactivate companies |
| **Kế toán viên** | ACCOUNTANT | Creates/Posts invoices/vouchers; cannot suspend companies |
| **Kiểm toán viên** | AUDITOR | Read-only access; audit log review; cannot modify data |
| **Nhân viên hệ thống** | ADMIN | First-user setup; user creation; password reset; role assignment |

### 2.2 Regulatory Drivers

| Law | Implication |
|-----|-----------|
| Luật Kế toán 2015 Art. 16 | Kế toán trưởng phải cóLicense MKHMN; user must be registered |
| Luật Kế toán 2015 Art. 44 | 10-year retention of accounting records + operator logs |
| Luật Quản lý thuế 2019 Art. 6 | MST/tax entity must be verified per operator |
| Luật BHXH 2024 | BHXH code per entity; operator must be tracked |
| NĐ 13/2023/NĐ-CP | Data retention per user for audit purposes |
| Decree 02/2022/NĐ-CP | Electronic accounting; user operation logging |

### 2.3 Competitor Baseline

| Product | User Module | Roles | Self-Service | Audit Log |
|---------|------------|-------|--------------|-----------|
| Fast Accounting | Basic | 3 roles | Manual admin setup | Basic |
| MISA AMIS | Full | 5+ roles | Web-based | Comprehensive |
| **This system** | **Raw SQL users table** | **5 roles** | **CLI scripts only** | **Via audit_log** |

---

## 3. Scope

### 3.1 In Scope (v1)

- User entity with: id, email, role, is_active, last_login, created_at, updated_at
- Role enum: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR (per existing auth_service.py)
- Role hierarchy: ACCOUNTANT < CHIEF_ACCOUNTANT < ADMIN < AUDITOR < DIRECTOR
- User CRUD via CLI scripts (manage.py) and AuthService
- @casbin_required decorator on 8 API routes (company + invoice + voucher + system-config + audit-log)
- Audit logging of every user action (entity_type="RBAC" + entity_type="USER")
- First-admin creation (once-only, via create-admin CLI)
- Password reset, enable/disable, assign-role CLI commands
- User listing with role + status display

### 3.2 Out of Scope (v1)

- Social login / OAuth authentication (OpenID, Google, Facebook)
- Password complexity enforcement beyond basic format
- Multi-factor authentication (OTP, TOTP)
- Password expiration policy
- Role hierarchy re-ranking (fixed per business rule)
- Email verification / confirmation flow
- forgot-password self-service (admin-only reset only)
- LDAP/Active Directory integration
- SSO (Single Sign-On) federation

---

## 4. Business Objectives

| Obj ID | Objective | Success Metric | Priority |
|--------|-----------|----------------|----------|
| OBJ-01 | Every operator registered with valid role | 100% of users have role ≠ NULL; zero orphan sessions | P0 |
| OBJ-02 | Role hierarchy enforced at API boundary | @casbin_required denies unauthorized accesses | P0 |
| OBJ-03 | User creation limited to ADMIN | Only ADMIN can create/users assign roles | P0 |
| OBJ-04 | Account disable/reactivate works | disable_user/enable_user CLI + API works | P0 |
| OBJ-05 | Audit trail for all user changes | Every user CRUD action in audit_log with before/after | P0 |
| OBJ-06 | MST/tax validation tied to operators | Responsible accountant linked to company | P1 |
| OBJ-07 | BHXH code tracked per operator | BHXH agency code stored per user profile | P1 |
| OBJ-08 | System operates without pycasbin crash | Fallback never blocks legitimate users | P0 |

---

## 5. Non-Functional Requirements

| NFR-ID | Requirement | Target | Priority |
|--------|-------------|--------|----------|
| NFR-01 | User lookup by email | <5ms indexed query | P0 |
| NFR-02 | User create/delete latency | <500ms CLI; <200ms API | P1 |
| NFR-03 | Password hash storage | SHA-256 (current) → bcrypt (≥12) in next version | P2 |
| NFR-04 | Tenant isolation at user level | User can only manage own profile + assigned scope | P1 |
| NFR-05 | Concurrent user edits | Optimistic locking via config_version | P1 |
| NFR-06 | MB per user record | <1KB (email + role + flags) | P2 |
| NFR-07 | Session termination | Immediate on disable; within 5 min on role change | P1 |
| NFR-08 | Audit log retention | ≥10 years per Luật Kế toán 2015 Art. 44 | P0 |

---

## 6. Assumptions

| ASM-ID | Assumption | Risk if False |
|--------|-----------|---------------|
| ASM-01 | First user to register becomes ADMIN (via create-admin CLI) | No admin = no user management possible |
| ASM-02 | Role enum is fixed: ACCOUNTANT/CHIEF_ACCOUNTANT/ADMIN/AUDITOR/DIRECTOR | New roles require code + RBAC model update |
| ASM-03 | pycasbin fallback sufficiently covers RBAC needs | Unauthorized access possible if fallback misconfigured |
| ASM-04 | Single deployment: one system per company (v1) | Multi-company user scoping not active |
| ASM-05 | MST validation already in Company module | Operator MST must match company MST for ACCOUNTANT+ roles |
| ASM-06 | AUDITOR is read-only by design | Cannot write invoices/vouchers/audit config |

---

## 7. Dependencies

| DEP-ID | Dependency | Owner | Risk |
|--------|-----------|-------|------|
| DEP-01 | AuthService users table + raw SQL | Dev team | Table schema may change; no SQLAlchemy model |
| DEP-02 | @casbin_required decorator on API routes | Dev team | Falls back to DEFAULT_ALLOWED_ROUTES if pycasbin fails |
| DEP-03 | CLI scripts (manage.py) for user CRUD | Dev team | No web UI for user management in v1 |
| DEP-04 | AuditLogService for user change logging | Dev team | Missing audit = compliance gap |
| DEP-05 | Role hierarchy CSV (rbac_policy.csv) | Dev team | Hierarchy anomaly: AUDITOR level > ADMIN but read-only |
| DEP-06 | Flask-Login current_user for role detection | Dev team | Test contexts may not have authenticated user |

---

## 8. Acceptance Criteria

- [ ] `users` table exists with columns: id, email, password, role, is_active, last_login, created_at, updated_at
- [ ] Role enum covers: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR
- [ ] create-admin CLI creates first admin (idempotent check: raises ValueError if admin exists)
- [ ] create-user CLI creates user with valid role; raises ValueError for invalid role
- [ ] assign-role CLI assigns role to user; raises LookupError if user not found
- [ ] enable-user CLI enables disabled account; raises LookupError if user not found
- [ ] disable-user CLI disables active account; raises LookupError if user not found
- [ ] list-users CLI lists all users with email, role, is_active, last_login
- [ ] reset-password CLI resets user password; raises LookupError if user not found
- [ ] @casbin_required decorator on all 8 API routes (company: 6 + invoice: 4 + voucher: 3 + system-config: 2 + audit-log: 2, with overlap)
- [ ] Every user CRUD action logged to audit_log with entity_type="USER"
- [ ] No user can have role= NULL; default='ACCOUNTANT' at table level
- [ ] System does not crash when pycasbin unavailable (fallback active)
- [ ] AUDITOR role: read-only (no write/delete policies in @casbin_required)
- [ ] Password stored as SHA-256 hash (current); bcrypted in future version

---

## 9. Open Questions

| Q | Owner | Needed By |
|---|-------|-----------|
| Will v1 support web UI for user management, or CLI-only? | Product | Before Phase 2 API design |
| Should password hashing upgrade to bcrypt be in v1 or v2? | CA | Before PROD deployment |
| How to handle AUDITOR read-only anomaly vs role level 4 > ADMIN? | CA | Before first PROD deployment |
| Should user profile store BHXH code, tax agency, responsibility fields? | CA | Before Phase 2 |
| How to enforce "user can only access company assigned to their role"? | Dev team | Before multi-company v2 |
| Should email verification flow be added in v1 or omitted? | Product | Before first PROD deployment |

---