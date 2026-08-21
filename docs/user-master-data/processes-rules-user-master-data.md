# Processes & Rules: User Master Data Module

## 1. User Lifecycle Processes

### 1.1 create-admin (CLI) — One-Time, Mandatory

**When run:** Fresh deployment, no users in `users` table
**Who can run:** Nobody — this is the first-step setup

```
1. AuthService.create_admin() executes
2. Query: SELECT COUNT(*) FROM users WHERE role = 'ADMIN'
3. If result > 0: raise ValueError("Admin user already exists")
4. Generate temp_password = secrets.token_urlsafe(16)
5. password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
6. INSERT INTO users (email, password, role, is_active, last_login, created_at, updated_at)
   VALUES ('admin@sme-acct.local', password_hash, 'ADMIN', 1, now, now, now)
7. Commit
8. Return _Admin object: id=1, email='admin@sme-acct.local', role='ADMIN', is_active=True
```

**Idempotency:** Not idempotent — raises ValueError if admin already exists. Use `reset-password` or `assign-role` instead.

### 1.2 create-user (CLI)

```
1. AuthService.create_user(email, role, password?) executes
2. valid_roles = {"ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR"}
3. If role ∉ valid_roles: raise ValueError(f"Invalid role '{role}'...")
4. Query: SELECT COUNT(*) FROM users WHERE email = :email
5. If count > 0: raise ValueError(f"User with email '{email}' already exists.")
6. If password is None: password = secrets.token_urlsafe(16)
7. password_hash = hashlib.sha256(password.encode()).hexdigest()
8. INSERT INTO users (...) VALUES (:email, :password_hash, :role, 1, :now, :now, :now)
9. Commit
10. Return _User object with id, email, role, is_active, last_login
```

### 1.3 assign-role (CLI)

```
1. AuthService.assign_role(user_identifier, role) executes
2. valid_roles = same set
3. If role ∉ valid_roles: raise ValueError
4. Try by email first: UPDATE users SET role = :role WHERE email = :email
5. If rowcount == 0: Try by ID: UPDATE users SET role = :role WHERE id = :uid
6. If rowcount == 0: raise LookupError(f"User '{user_identifier}' not found")
7. Commit
```

### 1.4 enable-user (CLI)

```
1. AuthService.enable_user(user_identifier) executes
2. Try by email: UPDATE users SET is_active = 1 WHERE email = :email
3. If rowcount == 0: Try by ID: UPDATE users SET is_active = 1 WHERE id = :uid
4. If rowcount == 0: raise LookupError(f"User '{user_identifier}' not found")
5. Commit
```

### 1.5 disable-user (CLI)

```
1. AuthService.disable_user(user_identifier) executes
2. Try by email: UPDATE users SET is_active = 0 WHERE email = :email
3. If rowcount == 0: Try by ID: UPDATE users SET is_active = 0 WHERE id = :uid
4. If rowcount == 0: raise LookupError(f"User '{user_identifier}' not found")
5. Commit
```

### 1.6 reset-password (CLI)

```
1. AuthService.reset_password(user_identifier, new_password) executes
2. password_hash = hashlib.sha256(new_password.encode()).hexdigest()
3. Try by email: UPDATE users SET password = :pw WHERE email = :email
4. If rowcount == 0: Try by ID: UPDATE users SET password = :pw WHERE id = :uid
5. If rowcount == 0: raise LookupError(f"User '{user_identifier}' not found")
6. Commit
```

### 1.7 list-users (CLI)

```
1. AuthService.list_users() executes
2. SELECT id, email, role, is_active, last_login FROM users
3. Format: email (30s) + role (15s) + status (8s) + last_login
4. Return list of dicts
```

---

## 2. RBAC Rules (Flask built-in — no Casbin, no pycasbin)

### 2.1 Role Hierarchy

| Role | Level | Can Access |
|------|-------|-----------|
| ACCOUNTANT | 1 | Own company's invoices/vouchers (own company_id only) |
| CHIEF_ACCOUNTANT | 2 | Company financial operations: suspend/reactivate, all invoices/vouchers |
| ADMIN | 3 | Full system: all companies, all users, all configurations |
| AUDITOR | 4 | **Read-only**: audit_log, company details, invoice/voucher read |
| DIRECTOR | 5 | System owner: all entities, all configurations, user management |

**Anomaly:** AUDITOR level(4) > ADMIN level(3), but AUDITOR is **read-only** (no write/delete policies).

### 2.2 Role-based Access (Flask built-in)

| Route Pattern | Roles |
|---|---|
| `api.v1.invoice.*` | {ACCOUNTANT, CHIEF_ACCOUNTANT} (per Flask built-in role check) |
| `api.v1.voucher.*` | {ACCOUNTANT, CHIEF_ACCOUNTANT} (per Flask built-in role check) |
| `api.v1.system-config.*` | {ADMIN} |
| `api.v1.audit-log.*` | {AUDITOR, CHIEF_ACCOUNTANT} |

### 2.3 RBAC Enforcement Pattern (Flask built-in)

1. Get user role from `flask_login.current_user.role`
2. Check if user is authenticated via `@login_required`
3. If allowed_roles specified: check `current_user.role in allowed_roles` → 403 if not
4. Log RBAC decision to audit_log
5. If not allowed: 403 `RBAC_DENIED`
6. Else: proceed to route handler

### 2.4 AUDITOR Read-Only Enforcement

- No write access for AUDITOR on `/api/v1/audit-log` write endpoints
- `@login_required + current_user.role == "AUDITOR"` on read endpoints only (GET, LIST)
- Attempt to POST/PUT/DELETE as AUDITOR → 403 RBAC_DENIED
- Exception: CHIEF_ACCOUNTANT can access audit-log (has write policies)

### 2.5 MST/Company Cross-Reference Rule (v1)

- ACCOUNTANT and CHIEF_ACCOUNTANT can only create/post invoices/vouchers for **their own company** (scoped by `company_id`)
- System checks: `Company.status ≠ SUSPENDED/DISSOLVED` before allowing invoice/voucher creation
- User's `company_id` (future v2) or implicit company from auth session (v1 single-company)

---

## 3. Data Validation Rules

### 3.1 Email Validation

| Pattern | Error |
|---------|-------|
| `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` | INVALID_EMAIL: "Định dạng email không hợp lệ" |
| Unique across `users` table | EMAIL_TAKEN: "Email này đã được đăng ký" |
| Max 120 chars (DB column) | same |

### 3.2 Role Validation

| Value | Error |
|-------|-------|
| Not in {ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR} | INVALID_ROLE: "Vai trò không hợp lệ" |
| ADMIN when admin already exists | ADMIN_EXISTS: "Admin đã tồn tại" |
| Role change that would leave system without admin | CANNOT_DEACTIVATE_LAST_ADMIN |

### 3.3 Password Validation (current SHA-256; future bcrypt)

| Rule | Error |
|------|-------|
| Min 8 characters | PASSWORD_TOO_SHORT: "Mật khẩu ít nhất 8 ký tự" |
| At least 1 letter + 1 number | PASSWORD_NO_MIX: "Mật khẩu phải chứa chữ cái + số" (v2) |
| Max 128 chars (hash length) | same |

### 3.4 User Status Rules

| Condition | Action |
|-----------|--------|
| `is_active = 0` → user cannot log in | Session invalidated on next request |
| `is_active = 1` → user can log in | Normal access |
| Attempt to deactivate last ADMIN → blocked | 409 CANNOT_DEACTIVATE_LAST_ADMIN |
| User disables own account → blocked without ADMIN co-sign | 403 SELF_DISALLOWED |
| User re-enables own disabled account → allowed if authenticated as admin | Normal flow |

---

## 4. Audit Logging Rules (from audit_log service)

| Field | Value | Source |
|-------|-------|--------|
| `entity_type` | "USER" or "RBAC" | Depends on action |
| `entity_id` | resource path (e.g., `/api/v1/users/123`) | From decorator |
| `action` | "CREATE" | user_create |
| | "UPDATE" | user_update, role_assign |
| | "DELETE" | (not used — soft-delete only) |
| | "ALLOW" / "DENY" | RBAC decision |
| `field_name` | column name changed (e.g., "role", "is_active") | From service |
| `before_value` | old value (e.g., "accountant") | From SQL UPDATE |
| `after_value` | new value (e.g., "chief_accountant") | From SQL UPDATE |
| `actor_id` | UUID of user performing action | From `current_user.id` |
| `actor_ip` | Client IP address | From `request.remote_addr` |
| `actor_user_agent` | Browser/APP version | From `request.user_agent.string` |
| `checksum` | SHA-256 hash of `actor_id:entity_id:action:role` | Computed in `_log_rbac_decision` pattern |
| `destroyed_at` | NULL = active; set when record archived | From audit_log model |

**Retention:** ≥10 years per Luật Kế toán 2015 Art. 44; never deleted (WORM).

---

## 5. Security Rules (from security-and-hardening skill)

| Rule | Enforcement |
|------|------------|
| Validate all external input at boundary | User input validated in AuthService + WTForms |
| Parameterize all database queries | SQLAlchemy ORM + parameterized queries in AuthService |
| Hash passwords with bcrypt/scrypt/argon2 | Currently SHA-256; roadmap to bcrypt (≥12 rounds) |
| Set security headers (CSP, HSTS, etc.) | Flask-Talisman (when DEBUG=False) |
| Use httpOnly, secure, sameSite cookies | Flask-Login session cookies |
| Never trust client-side validation | All validation server-side in AuthService |
| Rate limit auth endpoints | Not yet implemented; roadmap item |
| Log all security-relevant events | Every user CRUD + RBAC decision → audit_log |

---

## 6. Role Assignment Rules (Hard-coded)

| From/To | ACCOUNTANT | CHIEF_ACCOUNTANT | ADMIN | AUDITOR | DIRECTOR |
|---------|-----------|-----------------|-------|---------|----------|
| **ACCOUNTANT** | — | ✅ (upgrade) | ✅ (upgrade) | ❌ | ❌ |
| **CHIEF_ACCOUNTANT** | ⬇️ (downgrade) | — | ✅ (upgrade) | ❌ | ❌ |
| **ADMIN** | ⬇️ (downgrade) | ⬇️ (downgrade) | — | ✅ (downgrade to read-only) | ✅ (upgrade) |
| **AUDITOR** | ⬇️ (downgrade) | ⬇️ (downgrade) | ⬇️ (downgrade) | — | ❌ (cannot become DIRECTOR without ADMIN) |
| **DIRECTOR** | ⬇️ (downgrade) | ⬇️ (downgrade) | ⬇️ (downgrade) | ❌ (cannot downgrade ADMIN without cause) | — |

**Key constraints:**
- DIRECTOR can downgrade any role
- ADMIN can downgrade to ACCOUNTANT/CHIEF_ACCOUNTANT
- AUDITOR can only downgrade to lower read-only roles (never write)
- System never auto-downgrade ADMIN to lower role without explicit assign-role action

---