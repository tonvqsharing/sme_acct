# Data Flows, Workflows & User Journeys: User Master Data Module

## 1. Data Flows (DF-xx)

### DF-01: User Creation Flow (create-admin → first admin)

```
CLI: create-admin
     │
     ▼
AuthService.create_admin()
     │
     ├─► SELECT COUNT(*) FROM users WHERE role='ADMIN'
     │    │
     │    ├─► count > 0: raise ValueError (admin exists)
     │    └─► count == 0: continue
     │
     ├─► secrets.token_urlsafe(16) → temp_password
     │
     ├─► hash = SHA-256(temp_password)
     │
     ├─► INSERT INTO users (email, password, role, is_active, last_login, created_at, updated_at)
     │    VALUES ('admin@sme-acct.local', hash, 'ADMIN', 1, now, now, now)
     │
     ├─► db.session.commit()
     │
     ├─► Emit audit_log: entity_type="USER", action="CREATE", before=NULL, after=full_user_row
     │    actor_id=1, actor_ip=request.remote_addr, actor_user_agent=...
     │    checksum=SHA256("1:/api/v1/users:CREATE:ADMIN")
     │
     └─► Return _Admin object to caller
```

**Data at each step:**
- Before: empty users table, no admin context
- After: 1 row in users table; audit_log has 1 USER CREATE entry

---

### DF-02: User Creation Flow (create-user → new operator)

```
CLI: create-user --email u1@sme-acct.local --role ACCOUNTANT
     │
     ▼
AuthService.create_user(email, role, password?)
     │
     ├─► valid_roles check → ACCOUNTANT OK
     │
     ├─► SELECT COUNT(*) FROM users WHERE email='u1@sme-acct.local'
     │    │
     │    ├─► count > 0: raise ValueError (email taken)
     │    └─► count == 0: continue
     │
     ├─► If password is None: password = secrets.token_urlsafe(16)
     │
     ├─► hash = SHA-256(password)
     │
     ├─► INSERT INTO users (email, password, role, is_active, last_login, created_at, updated_at)
     │    VALUES ('u1@sme-acct.local', hash, 'ACCOUNTANT', 1, now, now, now)
     │
     ├─► db.session.commit()
     │
     ├─► Emit audit_log: entity_type="USER", action="CREATE", before=NULL, after={email, role, is_active}
     │    actor_id=ADMIN_ID, actor_ip=..., actor_user_agent=...
     │    checksum=SHA256("{actor_id}:/api/v1/users:CREATE:{role}")
     │
     └─► Return _User object {id, email, role, is_active, last_login}
```

---

### DF-03: Role Assignment Flow (assign-role)

```
CLI: assign-role --user u1@sme.acct.local --role CHIEF_ACCOUNTANT
     │
     ▼
AuthService.assign_role(user_identifier, role)
     │
     ├─► valid_roles check → CHIEF_ACCOUNTANT OK
     │
     ├─► Try: UPDATE users SET role='CHIEF_ACCOUNTANT' WHERE email='u1@sme-acct.local'
     │    │
     │    ├─► rowcount > 0: success → continue
     │    └─► rowcount == 0: Try: UPDATE users SET role='CHIEF_ACCOUNTANT' WHERE id=uid
     │           │
     │           ├─► rowcount > 0: success → continue
     │           └─► rowcount == 0: raise LookupError (user not found)
     │
     ├─► db.session.commit()
     │
     ├─► Emit audit_log: entity_type="USER", action="UPDATE", field_name="role"
     │    before_value="ACCOUNTANT", after_value="CHIEF_ACCOUNTANT"
     │    actor_id=ADMIN_ID, after_value="CHIEF_ACCOUNTANT"
     │    checksum=SHA256("{actor_id}:role:UPDATE:CHIEF_ACCOUNTANT")
     │
     └─► Return success message: "Role 'CHIEF_ACCOUNTANT' assigned to {email}"
```

---

### DF-04: Enable/Disable User Flow

```
CLI: disable-user --user u1@sme-acct.local
     │
     ▼
AuthService.disable_user(user_identifier)
     │
     ├─► Try: UPDATE users SET is_active=0 WHERE email='u1@sme-acct.local'
     │    │
     │    ├─► rowcount > 0: success → continue
     │    └─► rowcount == 0: Try: UPDATE users SET is_active=0 WHERE id=uid
     │           │
     │           ├─► rowcount > 0: success → continue
     │           └─► rowcount == 0: raise LookupError (user not found)
     │
     ├─► db.session.commit()
     │
     ├─► Emit audit_log: entity_type="USER", action="UPDATE", field_name="is_active"
     │    before_value=1, after_value=0
     │    actor_id=ADMIN_ID, checksum=SHA256("{actor_id}:is_active:UPDATE:0")
     │
     └─► Return: "User {email} disabled successfully"
```

**Same flow for enable-user**, but `is_active=1` and action="USER_ENABLED".

---

### DF-05: Password Reset Flow

```
CLI: reset-password --user u1@sme-acct.local --new-password NewPass123!
     │
     ▼
AuthService.reset_password(user_identifier, new_password)
     │
     ├─► hash = SHA-256("NewPass123!")
     │
     ├─► Try: UPDATE users SET password=:hash WHERE email=:email
     │    │
     │    ├─► rowcount > 0: success → continue
     │    └─► rowcount == 0: Try: UPDATE users SET password=:hash WHERE id=:uid
     │           │
     │           ├─► rowcount > 0: success → continue
     │           └─► rowcount == 0: raise LookupError (user not found)
     │
     ├─► db.session.commit()
     │
     ├─► Emit audit_log: entity_type="USER", action="UPDATE", field_name="password"
     │    before_value=NULL (never stored in plaintext), after_value=hash
     │    actor_id=ADMIN_ID, checksum=SHA256("{actor_id}:password:UPDATE:{hash_suffix}")
     │
     └─► Return: "Password reset for {email} successfully"
```

---

### DF-06: User Listing Flow

```
CLI: list-users
     │
     ▼
AuthService.list_users()
     │
     ├─► SELECT id, email, role, is_active, last_login FROM users
     │
     ├─► fetchall() → list of rows
     │
     ├─► Format each row:
     │    {email:30s}  role:{role:15s}  status:{ACTIVE|DISABLED:8s}  last_login={...or'never'}
     │
     └─► Return formatted list to caller
```

---

## 2. Workflows (WF-xx)

### WF-01: Fresh Deployment Workflow (User Onboarding)

```
START → Run: flask db init │ flask db migrate │ flask db upgrade
     │
     ▼
Run: scripts/manage.py create-admin
     │
     ├─► If admin exists: error → use reset-password
     └─► Admin created: admin@sme-acct.local / temp-pass
     │
     ▼
Run: scripts/manage.py create-user --email admin@sme-acct.local --role ADMIN
     │     (or: system auto-creates from create-admin step above)
     │
     ▼
Set password on first login (temp password → change password)
     │
     ▼
Configure company: (separate Company module workflow)
     │
     ▼
WELCOME: System ready for operator onboarding
```

**Success criteria:** Admin user exists in `users` table; Flask-Login session active; audit_log table operational.

---

### WF-02: User Lifecycle Management Workflow

```
               +----------------------+
               |  Admin logged in     |
               +----------+-----------+
                          |
                          ▼
               +----------------------+
               |  User management UI  | (or: CLI scripts)
               +----------+-----------+
                          |
       +-----------------+-----------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Create new user   |            |  Assign role to user |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Verify email not  |            |  Validate role in    |
|  in use (409)      |            |  hierarchy (level)   |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Write to users    |            |  Emit ROLE_ASSIGNED  |
|  table (AuthService)|           |  to audit_log        |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Invalidate caches |            |  Return success      |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
               +----------------------+
               |  LOG OUT / NEXT      |
               +----------------------+
```

---

### WF-03: Account Suspension/Reactivation Workflow

```
               +----------------------+
               |  Admin decides:      |
               |  suspend/reactivate  |
               +----------+-----------+
                          |
                          ▼
+--------------------+            +----------------------+
|  Suspend user:     |            |  Reactivate user:    |
|  POST /users/{id}/ |            |  POST /users/{id}/   |
|  disable           |            |  enable              |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Check: is this   |            |  Check: user exists? |
|  the only ADMIN?   |            |  (404 if not found)  |
|  (409 if yes)      |            +----------------------+
       |                                   |  is_active was 0?   |
       |                                   |  (set is_active=1) |
       |                                   +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  UPDATE users SET  |            |  UPDATE users SET    |
|  is_active=0       |            |  is_active=1         |
|  config_version++  |            |  config_version++    |
+--------------------+            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Emit audit_log:   |            |  Emit audit_log:     |
|  USER_DISABLED/    |            |  USER_ENABLED        |
|  USER_ENABLED      |            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Invalidate session|            |  Re-enable login     |
|  tokens (5 min)    |            +----------------------+
       |                                   |
       ▼                                   ▼
               +----------------------+
               |  Return success      |
               +----------------------+
```

---

### WF-04: Password Reset Workflow

```
               +----------------------+
               |  Admin initiates     |
               |  password reset      |
               +----------+-----------+
                          |
                          ▼
+--------------------+            +----------------------+
|  Verify: user      |            |  Verify: new password|
|  exists (404 if    |            |  meets requirements  |
|  not found)        |            +----------------------+
       |                                   |
       ▼                                   ▼
+--------------------+            +----------------------+
|  UPDATE users SET  |            |  hash = SHA-256(new) |
|  password=:hash    |            +----------------------+
|  config_version++  |            |  (not stored plaintext)|
+--------------------+            |  Emit PASSWORD_RESET |
       |                                   |  to audit_log        |
       ▼                                   ▼
+--------------------+            +----------------------+
|  Return: "Password  |            |  Return: "Password   |
|  reset for {email} |            |  reset for {email}   |
|  successfully"     |            |  successfully"       |
       |                                   |
       ▼                                   ▼
               +----------------------+
               |  User logs in with   |
               |  new password        |
               +----------------------+
```

---

## 3. User Journeys (UJ-xx)

### UJ-01: Fresh Deployment — First Admin Onboarding (BA Lead Perspective)

```
[Step 1] System freshly deployed, no users in database
      │
      ▼
[Step 2] BA Lead runs: scripts/manage.py create-admin
      │
      │   ┌─────────────────────────────────────────────────────────┐
      │   │  Behind the scenes:                                     │
      │   │  1. SELECT COUNT(*) FROM users WHERE role='ADMIN'      │
      │   │  2. count=0 → continue                                  │
      │   │  3. temp_password = "Kx9#mP2vQ7rT1wL5"               │
      │   │  4. SHA-256 hash = "a1b2c3d4e5f6..."                │
      │   │  5. INSERT INTO users (email, password, role, ...)     │
      │   │  6. commit                                              │
      │   │  7. audit_log: USER CREATE, actor=anonymous→1         │
      │   │       (checksum logged for integrity)                 │
      │   └─────────────────────────────────────────────────────────┘
      │
      ▼
[Step 3] System returns: "Admin created: admin@sme-acct.local (id=1) — role=ADMIN, can reset passwords & assign roles"
      │
      ▼
[Step 4] BA Lead logs in with temporary password (first-time login forces password change)
      │
      ▼
[Step 5] BA Lead assigns roles to other operators:
      - scripts/manage.py create-user --email ca@sme-acct.local --role CHIEF_ACCOUNTANT
      - scripts/manage.py create-user --email acct@sme-acct.local --role ACCOUNTANT
      - scripts/manage.py assign-role --user auditor@sme-acct.local --role AUDITOR
      │
      ▼
[Step 6] All operators can log in with their credentials
      │
      ▼
[Step 7] System enforces RBAC via @login_required + current_user.role on all API routes
      │
      ▼
[Step 8] Every action logged to audit_log with full trail (who, what, when, checksum)
      │
      ▼
[Step 9] PROD ENV: system operational with user RBAC enforcement via fallback
      │
      ▼
END: Fresh deployment complete; user master data operational
```

---

### UJ-02: Daily Operation — Accountant Workflow (Chief Accountant Perspective)

```
[Step 1] SA (Staff Accountant) logs in with credentials
      │
      │  Behind the scenes:
      │  1. Flask-Login: current_user.id, current_user.role = "accountant"
      │  2. @login_required + current_user.role == "ACCOUNTANT" check
      │  3. If allowed → proceed; if denied → 403 RBAC_DENIED
      │
      ▼
[Step 2] SA navigates to: POST /api/v1/invoices (create invoice)
      │
      │  Behind the scenes:
      │  1. Role=ACCOUNTANT, resource=/api/v1/invoices, action=POST
      │  2. current_user.role in ("ACCOUNTANT", "CHIEF_ACCOUNTANT") → ALLOWED
      │  3. @login_required allows access
      │
      ▼
[Step 3] SA fills invoice form + submits
      │
      ▼
[Step 4] System validates: company_id FK, MST format, account codes, VAT rates
      │
      ▼
[Step 5] System: POST /api/v1/invoices → 201 Created
      │
      ▼
[Step 6] System emits audit_log: entity_type="INVOICE", action="CREATE", before=NULL, after=invoice_row
      │    actor_id=SA's user_id, actor_ip=SA's IP, actor_user_agent=SA's browser
      │    checksum=SHA256("{actor_id}:/api/v1/invoices:CREATE:accountant")
      │
      ▼
[Step 7] SA sees: "Invoice created successfully; invoice #INV-001"
      │
      ▼
[Step 8] Every subsequent action (post voucher, query report) similarly logged
      │
      ▼
[Step 9] End of day: SA reviews audit log for compliance; all entries intact (WORM, ≥10y retention)
      │
      ▼
[Step 10] SA logs out; session invalidated if is_active was toggled
```

---

### UJ-03: Auditor Read-Only Journey

```
[Step 1] AU (Auditor) logs in with credentials
      │
      │  Behind the scenes:
      │  1. current_user.role = "auditor"
      │  2. @login_required + current_user.role == "AUDITOR" check on /api/v1/audit-log GET
      │  3. AUDITOR allowed on GET → allowed (read-only)
      │
      ▼
[Step 2] AU navigates to: GET /api/v1/audit-log (list all audit entries)
      │
      │  Behind the scenes:
      │  1. Role=AUDITOR, resource=/api/v1/audit-log, action=GET
      │  2. current_user.role == "AUDITOR" → allowed (read-only)
      │  3. @login_required returns 200 + audit data
      │
      ▼
[Step 3] AU reviews audit log entries for compliance
      │
      ▼
[Step 4] AU attempts: POST /api/v1/audit-log (create new audit entry)
      │
      │  Behind the scenes:
      │  1. Role=AUDITOR, resource=/api/v1/audit-log, action=POST
      │  2. current_user.role == "AUDITOR" → DENY (read-only)
      │  3. @login_required returns 403 RBAC_DENIED
      │    Error: "RBAC denied: role 'AUDITOR' cannot 'post' '/api/v1/audit-log'"
      │
      ▼
[Step 5] AU sees: 403 Forbidden with code RBAC_DENIED
      │
      ▼
[Step 6] AU continues reading; cannot modify any audit data (WORM compliance)
      │
      ▼
[Step 7] End of session; AU logs out
```

---

### UJ-04: Admin Role Management Journey

```
[Step 1] Admin (DIRECTOR or ADMIN) logs in
      │
      │  Behind the scenes:
      │  1. current_user.role = "admin" or "director"
      │  2. @login_required + current_user.role in allowed_roles check
      │
      ▼
[Step 2] Admin navigates to: GET /api/v1/users (list all users)
      │
      │  Behind the scenes:
      │  1. RBAC check: admin can access user listing
      │  2. Return list of {email, role, is_active, last_login}
      │
      ▼
[Step 3] Admin selects user to modify + chooses action:
      - Assign new role
      - Enable/disable account
      - Reset password
      - Deactivate (if not the only ADMIN)
      │
      ▼
[Step 3] Admin submits action (e.g., assign-role)
      │
      ▼
[Step 4] System validates:
      - User exists (404 if not)
      - Role valid (400 if not)
      - Not making things worse (409 if would leave system without admin)
      │
      ▼
[Step 4] System executes:
      - AuthService.assign_role(user_id, new_role)
      - UPDATE users SET role=new_role, config_version=config_version+1
      - Emit audit_log: ROLE_ASSIGNED
      │
      ▼
[Step 5] System returns: "Role 'CHIEF_ACCOUNTANT' assigned to {email}"
      │
      ▼
[Step 5] Admin sees confirmation; all actions fully auditable
      │
      ▼
[Step 6] End of journey; complete trail from user creation to role assignment
```