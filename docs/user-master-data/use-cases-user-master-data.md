# Use Cases: User Master Data Module

Personas:
- **A** — Admin / Giám đốc (system owner)
- **CA** — Chief Accountant / Kế toán trưởng
- **SA** — Staff Accountant / Kế toán viên
- **AU** — Auditor / Kiểm toán viên

---

## UC-01: Initial User Setup (One-Time, Mandatory)

**Actor:** A (first run) or CA (subsequent runs with ADMIN confirmation)
**Preconditions:** System fresh deployment; no users exist in `users` table

### Happy Path

1. A accesses system first time; system detects no users
2. System routes to `/users/new` setup wizard (or invokes `create-admin` CLI)
3. A fills: email, role=ADMIN (system enforces only ADMIN can create first user)
4. A sets temporary password (or system generates random 16-char)
5. System hashes password with SHA-256; writes user to `users` table
6. System: `is_active=1`, `last_login=NULL`, `config_version=1`
7. A confirms: "Admin user created; ready for operator onboarding"
8. System emits `USER_CREATED` audit event (entity_type="USER")

### Alternative Path — Subsequent Admin Creation

1. A or CA with ADMIN role accesses `/users/create`
2. System checks: admin already exists?
   - **YES**: Route to `reset-password` or `assign-role` instead
   - **NO**: Proceed to step 3 of Happy Path

### Exception Paths

- **EX-01:** Email already exists → 409 EMAIL_TAKEN: "Email này đã được đăng ký"
- **EX-02:** Email format invalid → 422 INVALID_EMAIL: "Định dạng email không hợp lệ (ten@don-vi.vn)"
- **EX-03:** Attempt to create admin when admin already exists → 409 ADMIN_EXISTS: "Admin đã tồn tại — dùng reset-password thay vì create-admin lại"
- **EX-04:** Password too weak → 422 PASSWORD_WEAK: "Mật khẩu ít nhất 8 ký tự, chứa chữ cái + số" (v2 feature)

---

## UC-02: Create User (Admin Action)

**Actor:** A or CA with ADMIN role
**Preconditions:** Admin authenticated; at least one ADMIN exists in system

### Happy Path

1. A navigates: GET /users/create or invokes `create-user` CLI
2. A fills: email, role (ACCOUNTANT/CHIEF_ACCOUNTANT/ADMIN/AUDITOR/DIRECTOR), optional password
3. System validates: role is valid UserRole enum
4. System validates: email not already registered
5. System generates password if not provided (random 16-char)
6. System hashes password with SHA-256; writes user to `users` table
7. System: `is_active=1`, `last_login=NULL`, `created_by=A user id`, `config_version=1`
8. System emits `USER_CREATED` audit event (before/after values)
9. System returns: user id, email, role, temporary password (if newly generated)
10. A confirms: "User created successfully"

### Alternative Path — Household/Simplified

1. A selects role=ACCOUNTANT for new staff accountant
2. System defaults: `is_active=1`, fiscal-year/period scoping per company assignment (future v2)

### Exception Paths

- **EX-01:** Email already in use → 409 EMAIL_TAKEN (as above)
- **EX-02:** Invalid role → 400 INVALID_ROLE: "Vai trò không hợp lệ. Chọn: accountant, chief_accountant, admin, auditor, director"
- **EX-03:** Password policy violation → 422 PASSWORD_WEAK (v2)
- **EX-04:** Attempt to create user without ADMIN role → 403 RBAC_DENIED (as per @casbin_required)

---

## UC-03: Assign Role to User

**Actor:** A or CA with ADMIN role
**Preconditions:** Admin authenticated; target user exists; target user is not the only ADMIN

### Happy Path

1. A navigates: GET /users/{id}/assign-role or invokes `assign-role` CLI
2. A selects: new role for the user (ACCOUNTANT/CHIEF_ACCOUNTANT/ADMIN/AUDITOR/DIRECTOR)
3. System validates: role is valid UserRole enum
4. System updates: `users.role = new_role`; `config_version++`
5. System emits `ROLE_ASSIGNED` audit event (old_role, new_role, user_id, actor_id)
6. System returns: "Role '{new_role}' assigned to {email}"
7. A confirms: "Role updated successfully"

### Alternative Path — Role Hierarchy Check

1. A tries to assign DIRECTOR role to existing user
2. System validates: hierarchy allowed (any role can become DIRECTOR in v1)
3. Proceeds as Happy Path

### Exception Paths

- **EX-01:** User not found → 404 USER_NOT_FOUND: "Người dùng không tồn tại"
- **EX-02:** Attempt to assign role=ADMIN when admin already exists → 409 ADMIN_EXISTS (as EX-03 in UC-01)
- **EX-02:** Attempt to deactivate the only ADMIN → 409 CANNOT_DEACTIVATE_LAST_ADMIN: "Không thể vô hiệu hóa user ADMIN cuối cùng"
- **EX-03:** Actor attempts to assign role higher than own → 403 RBAC_DENIED (hierarchy check)
- **EX-04:** Actor assigns role to themselves with lower privilege → 403 SELF_ROLE_DECREASE: "Không thể giảm quyền của chính mình"

---

## UC-04: Enable/Disable User Account

**Actor:** A or CA with ADMIN|DIRECTOR role
**Preconditions:** Admin authenticated; target user exists

### Happy Path — Disable (Disable User)

1. A navigates: GET /users/{id}/disable or invokes `disable-user` CLI
2. System checks: target user ≠ actor (or actor has ADMIN|DIRECTOR)
3. System: `users.is_active = 0`; `config_version++`
4. System emits `USER_DISABLED` audit event (user_id, actor_id, previous_is_active)
5. System returns: "User {email} disabled successfully"
6. A confirms: "User account disabled"

### Happy Path — Enable (Enable User)

1. A navigates: GET /users/{id}/enable or invokes `enable-user` CLI
2. System checks: target user exists
3. System: `users.is_active = 1`; `config_version++`
4. System emits `USER_ENABLED` audit event (user_id, actor_id, previous_is_active)
5. System returns: "User {email} enabled successfully"
6. A confirms: "User account enabled"

### Exception Paths

- **EX-01:** User not found → 404 USER_NOT_FOUND (as above)
- **EX-02:** Attempt to disable the only ADMIN → 409 CANNOT_DEACTIVATE_LAST_ADMIN (as EX-02 in UC-03)
- **EX-03:** Actor disables own account without ADMIN co-action → 403 SELF_DISALLOWED: "Không thể vô hiệu hóa tài khoản của chính mình mà không có sự đồng ý của Admin"
- **EX-04:** Actor enables a disabled user without proper authorization → 403 RBAC_DENIED

---

## UC-05: Reset User Password

**Actor:** A or CA with ADMIN role
**Preconditions:** Admin authenticated; target user exists

### Happy Path

1. A navigates: GET /users/{id}/reset-password or invokes `reset-password` CLI
2. A provides: new plain-text password
3. System hashes password with SHA-256
4. System: `users.password = new_hash`; `config_version++`
5. System emits `PASSWORD_RESET` audit event (user_id, actor_id, password_changed_at)
6. System returns: "Password reset for {email}; temporary login with new password"
7. A confirms: "Password reset successfully"

### Exception Paths

- **EX-01:** User not found → 404 USER_NOT_FOUND (as above)
- **EX-02:** Password too weak (v2) → 422 PASSWORD_WEAK (as EX-04 in UC-01)
- **EX-03:** Actor is not ADMIN or DIRECTOR → 403 RBAC_DENIED

---

## UC-06: List Users

**Actor:** A with ADMIN role; CA with ADMIN role; SA with management scope
**Preconditions:** Admin authenticated

### Happy Path

1. A navigates: GET /users or invokes `list-users` CLI
2. System: `SELECT id, email, role, is_active, last_login FROM users`
3. System returns: paginated list of users with: email, role, is_active status, last_login
4. System formats: status = "ACTIVE" if is_active=1 else "DISABLED"
5. A reviews: user list displayed

### Alternative Path — Filter by Role

1. A adds query: `?role=accountant`
2. System: `WHERE role = 'accountant'` — returns only ACCOUNTANT users
3. Proceeds as Happy Path

### Exception Paths

- **EX-01:** Unauthorized access → 403 RBAC_DENIED (as per @casbin_required)

---

## UC-07: Change My Own Password (Self-Service)

**Actor:** Any authenticated user (A, CA, SA, AU)
**Preconditions:** User logged in via Flask-Login; knows current password

### Happy Path

1. User navigates: GET /users/change-password (or POST with current + new password)
2. User provides: current_password, new_password
3. System verifies: current_password matches stored hash for this user
4. System: `users.password = hash(new_password)`; `config_version++`
5. System emits `PASSWORD_CHANGED` audit event (user_id, actor_id = user_id)
6. System returns: "Password changed successfully; please re-login"
7. User re-logs in with new password

### Exception Paths

- **EX-01:** Current password incorrect → 401 UNAUTHORIZED: "Mật khẩu hiện tại không đúng"
- **EX-02:** New password too weak → 422 PASSWORD_WEAK (v2 feature)
- **EX-03:** New password same as current → 400 SAME_PASSWORD: "Mật khẩu mới phải khác mật khẩu hiện tại"

---