# Spec: User Master Data Module (User Management)

> Vietnamese SME Accounting System — User Entity Technical Specifications v0.1.0

---

## 1. Position in Architecture

```
src/
  domain/
    entities/           ← NEW: User entity + TaxId/AccountCode value objects
    exceptions/         ← NEW: UserNotFoundError, DuplicateEmailError, UserLockedError
    repositories/       ← NEW: UserRepositoryPort (abstract interface)
  application/
    ports/              ← NEW: UserRepositoryPort (interface)
    services/           ← NEW: AuthService (already exists; extend if needed)
  infrastructure/
    database/
      models.py         ← EXTEND: UserModel (SQLAlchemy) + migrate from raw SQL
    repositories/       ← NEW: SQLAlchemyUserRepository (adapter)
  presentation/
    api/                ← NEW: User API blueprints (CRUD + RBAC)
    ui/               ← NEW: User HTML templates (admin panel)
    forms/            ← NEW: WTForms for user CRUD
    serializers/       ← NEW: domain↔JSON serializers
```

**Critical:** User is a domain entity. Domain layer MUST NOT import Flask/SQLAlchemy. RBAC enforcement via `@casbin_required` at presentation layer only.

---

## 2. Domain Model

### 2.1 User Entity (`src/domain/entities/user.py`)

```python
@dataclass
class User:
    """Operator / user of the Vietnamese SME accounting system.

    Per Luật Kế toán 2015 Art. 16: Kế toán trưởng must be registered.
    Per Decree 02/2022/NĐ-CP: Electronic accounting operator logging.
    """

    id: UUID                    # PK
    email: str                  # Unique; login name; max 120 chars
    password: str               # Hashed (SHA-256 current; bcrypt future)
    role: UserRole              # Enum: ACCOUNTANT | CHIEF_ACCOUNTANT | ADMIN | AUDITOR | DIRECTOR
    is_active: bool             # Soft-disabled flag; TRUE = active
    last_login: datetime | None  # Timestamp; NULL never logged
    created_at: datetime        # Audit trail
    created_by: UUID            # Who created this user (admin id)
    updated_at: datetime        # Audit trail
    updated_by: UUID            # Who last updated this user (admin id)
    config_version: int        # Optimistic lock version
```

### 2.2 UserRole Enum (`src/domain/entities/base.py` — extend)

Add to existing base.py:

```python
class UserRole(Enum):
    """Roles per quy định nội bộ hệ thống SME accounting."""
    ACCOUNTANT = "accountant"          # Creates/postes invoices/vouchers
    CHIEF_ACCOUNTANT = "chief_accountant"  # Company financial oversight
    ADMIN = "admin"                    # System setup; user/role management
    AUDITOR = "auditor"                # Read-only; audit log review
    DIRECTOR = "director"              # System owner; full oversight
```

### 2.3 Supporting Value Objects (already in base.py)

No changes needed — TaxId and AccountCode already defined.

---

## 3. Port Interface

### 3.1 UserRepositoryPort (`src/application/ports/__init__.py` — extend)

```python
class UserRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User, actor: UUID) -> User: ...

    @abstractmethod
    def deactivate(self, user_id: UUID, actor: UUID) -> User: ...

    @abstractmethod
    def activate(self, user_id: UUID, actor: UUID) -> User: ...

    @abstractmethod
    def list_active(self) -> list[User]: ...

    @abstractmethod
    def list_by_role(self, role: UserRole) -> list[User]: ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool: ...
```

### 3.2 SQLAlchemyUserRepository Adapter (`src/infrastructure/repositories/` — new)

Adapts `UserRepositoryPort` to `SQLAlchemyUserRepository` using SQLAlchemy 2.0 models.

---

## 4. Database Schema

### 4.1 users (extend from raw SQL to SQLAlchemy 2.0 model)

Replace raw SQL table with SQLAlchemy 2.0 `UserModel` in `src/infrastructure/database/models.py`.

**Current raw SQL (auth_service.py:_ensure_users_table):**

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'ACCOUNTANT',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

**Target SQLAlchemy 2.0 UserModel:**

```python
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # hashed
    role: Mapped[UserRoleEnum] = mapped_column(
        SQLEnum(UserRoleEnum), nullable=False, default=UserRoleEnum.ACCOUNTANT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True  # self-referential: who created
    )

    # Constraints
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
```

**UserRoleEnum** added to models.py:

```python
class UserRoleEnum(enum.Enum):
    ACCOUNTANT = "accountant"
    CHIEF_ACCOUNTANT = "chief_accountant"
    ADMIN = "admin"
    AUDITOR = "auditor"
    DIRECTOR = "director"
```

### 4.2 Migration Plan (Phased)

| Phase | Action |
|-------|--------|
| Phase 1 | Add UserModel to models.py; create migration `flask db migrate`; `flask db upgrade` |
| Phase 2 | Backfill `company_id` FK from Company module (DEP-01 dependency) |
| Phase 3 | Update AuthService to use SQLAlchemyUserRepository instead of raw SQL |
| Phase 4 | Deprecate raw SQL `_ensure_users_table`; remove once all routes use ORM |

---

## 5. API Specification

### 5.1 Endpoints

| Method | Path | Auth | RBAC | Description |
|--------|------|------|------|-------------|
| `POST` | `/api/v1/users` | JWT | ADMIN | Create user (one-time setup + admin) |
| `GET` | `/api/v1/users` | JWT | ADMIN | List all users |
| `GET` | `/api/v1/users/{id}` | JWT | AUTH | User detail (own profile or ADMIN-only) |
| `PATCH` | `/api/v1/users/{id}` | JWT | ADMIN | Update user (role, active status, password) |
| `POST` | `/api/v1/users/{id}/suspend` | JWT | ADMIN|DIRECTOR | Disable user account |
| `POST` | `/api/v1/users/{id}/reactivate` | JWT | ADMIN|DIRECTOR | Enable user account |
| `POST` | `/api/v1/users/{id}/reset-password` | JWT | ADMIN | Reset user password |
| `DELETE` | `/api/v1/users/{id}` | JWT | ADMIN | Hard delete (admin-only; soft-deactivate preferred) |

### 5.2 Request/Response Schemas

**POST /api/v1/users (Create)**

```json
{
  "email": "accountant@sme-acct.local",
  "role": "accountant",
  "password": "TempPass123!",
  "is_active": true
}
```

**GET /api/v1/users/{id}**

```json
{
  "id": "uuid",
  "email": "accountant@sme-acct.local",
  "role": "accountant",
  "is_active": true,
  "last_login": "2026-08-17T10:30:00Z",
  "created_at": "2026-08-17T08:15:00Z",
  "created_by": "uuid",
  "updated_at": "2026-08-17T10:30:00Z",
  "updated_by": "uuid"
}
```

**PATCH /api/v1/users/{id}**

```json
{
  "role": "chief_accountant",
  "is_active": false
}
```

### 5.3 Error Responses

| HTTP | Code | Condition |
|------|------|-----------|
| 400 | INVALID_ROLE | Role not in enum |
| 409 | EMAIL_TAKEN | Email already registered |
| 403 | USER_NOT_AUTHORIZED | User has no access to this endpoint |
| 404 | USER_NOT_FOUND | User ID does not exist |
| 422 | PASSWORD_TOO_WEAK | Password doesn't meet complexity (v2 only) |
| 409 | CANNOT_DEACTIVATE_OWN_ACCOUNT | User cannot deactivate own account without ADMIN |

---

## 6. Validation Rules

### 6.1 At Domain Boundary (Construction Time)

| Field | Rule | Error |
|-------|------|-------|
| `email` | Required; valid email format; max 120 chars; unique across system | `DuplicateEmailError("Email đã được đăng ký")` |
| `password` | Required; min 8 chars; at least 1 letter + 1 number; hashed on save | `UserValidationError("Mật khẩu không đủ mạnh")` |
| `role` | Must be valid UserRole enum | `InvalidUserRoleError("Vai trò không hợp lệ")` |
| `is_active` | Boolean; default TRUE | same |
| `email` | Cannot change role → MST/tax cross-reference check (future) | same |

### 6.2 At Service Layer

| Rule | Enforcement |
|------|------------|
| First user becomes ADMIN | create-admin CLI: checks no admin exists; raises ValueError if admin already present |
| ADMIN cannot be deactivated by normal user | AuthService.disable_user: checks target role ≠ ADMIN unless actor is ADMIN or DIRECTOR |
| User cannot deactivate own account | PATCH /users/{id} with is_active=false: checks user_id ≠ actor_id unless actor has ADMIN|DIRECTOR |
| Password hash on creation | AuthService.create_user: hashes password with SHA-256 before INSERT |
| Last login tracked on successful login | Presentation middleware: updates User.last_login on each successful auth |

---

## 7. Migration Plan

### Phase 1 — Entity + Model + Migration

- [ ] Add `UserRoleEnum` to `src/infrastructure/database/models.py`
- [ ] Add `UserModel` to `src/infrastructure/database/models.py` (SQLAlchemy 2.0)
- [ ] Run `flask db migrate` — generates migration script
- [ ] Run `flask db upgrade` — applies new `users` table
- [ ] Verify: `users` table exists with correct columns + constraints

### Phase 2 — Repository Adapter + Service

- [ ] Create `SQLAlchemyUserRepository` in `src/infrastructure/repositories/`
- [ ] Implement all `UserRepositoryPort` methods via SQLAlchemy
- [ ] Update `AuthService` to use `SQLAlchemyUserRepository` instead of raw SQL
- [ ] Migrate `_ensure_users_table` to use new model (or deprecate)

### Phase 3 — API + RBAC

- [ ] Create `users_blueprint` in `src/presentation/api/`
- [ ] Add `@casbin_required` decorator on all user endpoints
- [ ] Update `DEFAULT_ALLOWED_ROUTES` in `rbac.py` with user endpoint policies
- [ ] Add audit logging for every user CRUD action (entity_type="USER")

### Phase 4 — UI + Templates

- [ ] Create user HTML templates (admin panel for user management)
- [ ] Create WTForms for user CRUD
- [ ] Wire forms to API blueprints
- [ ] Test: create user via web → audit log entry exists

### Phase 5 — Decommission Raw SQL

- [ ] Remove `_ensure_users_table` from `auth_service.py`
- [ ] Remove raw `CREATE TABLE users` SQL
- [ ] Remove `scripts/manage.py` user commands that use raw SQL
- [ ] Update `tests/` to use new `SQLAlchemyUserRepository`
- [ ] Run full test suite: all 94 tests pass

---

## 8. Open Questions

| Q | Owner | Needed By |
|---|-------|-----------|
| Should password complexity be enforced in v1 or deferred to v2? | CA | Before PROD deployment |
| Should `created_by` self-referencing FK be active in v1 or v2? | Dev team | Before multi-user deployment |
| Should `last_login` be tracked per-session or per-request? | Dev team | Before reporting/dashboard features |
| Should user profile store BHXH code, tax agency responsibility? | CA | Before Phase 2 |
| Should AUDITOR role have any write capability (e.g., approve audit items)? | CA | Before first PROD deployment |
| Should `email` be case-sensitive for uniqueness? | Dev team | Before first PROD deployment (MySQL defaults to case-insensitive) |

---