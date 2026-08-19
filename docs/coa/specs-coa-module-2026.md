# Technical Specifications: Chart of Accounts Module
## Vietnamese SME Accounting Application — v2026

**Status:** DRAFT — v1.0  
**Date:** 2026-08-18  
**Alignment:** BRD `brd-coa-module-2026.md`; Circular 99/2025/TT-BTC; Law on Accounting 2015  
**Codebase:** Flask + Clean Architecture; `src/domain/entities/` (NO sqlalchemy/web imports); `src/infrastructure/database/models.py`; `src/infrastructure/repositories/`; `src/application/services/`; `src/presentation/api/`

---

## 1. Domain Layer Entities (Pure Python — No SQLAlchemy/Flaimport)

### 1.1 `src/domain/entities/coa.py` — Account Aggregate Root

```python
"""Chart of Accounts domain entities (specs-coa-module-2026.md §1).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Law on Accounting 2015 Chap IV; Circular 99/2025/TT-BTC Art 11;
Circular 200/2014/TT-BTC Appendix II; account code format per TT99: ^\d{10}$
or ^\d{10}-\d{3}$.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from src.domain.entities.base import AccountCode, AccountCategory, AccountStatus
from src.domain.exceptions import (
    InvalidAccountCodeError,
    AccountCodeAlreadyExistsError,
    SystemAccountModificationError,
    RequiresChiefAccountantError,
)


# ── Enums ──────────────────────────────────────────────────────────────

class AccountCategory(str, Enum):
    """9 main categories per Vietnamese Accounting Standards (Circular 99 Art 11)."""
    ASSET = "Asset"
    RECEIVABLE = "Receivable"
    INVENTORY = "Inventory"
    FIXED_ASSET = "Fixed Asset"
    PAYABLE = "Payable"
    ACCRUED_EXPENSE = "Accrued Expense"
    REVENUE = "Revenue"
    OPERATING_EXPENSE = "Operating Expense"
    UNDISTRIBUTED_PROFIT = "Undistributed Profit"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    SUSPENDED = "Suspended"


class AccountTag(str, Enum):
    """7 mandatory tags per Circular 99; custom tags allowed with IGAP doc."""
    REVENUE = "Revenue"
    TAX_PAYABLE = "Tax Payable"
    FIXED_ASSET = "Fixed Asset"
    INVENTORY = "Inventory"
    COGS = "Cost of Goods Sold"
    OPERATING_EXPENSE = "Operating Expense"
    UNDISTRIBUTED_PROFIT = "Undistributed Profit"


# ── Value Objects ────────────────────────────────────────────────────

class AccountCode:
    """Validated Vietnamese account code.

    Format: ^\d{10}$  (e.g., 1001000001)  OR  ^\d{10}-\d{3}$ (e.g., 1001000001-001)
    Per TT99: leading digit 1-9 required: ^[1-9]\d{2}$ for 3-digit prefix,
    but full code always 10 digits with optional -3digit suffix.
    """

    __slots__ = ("value”,)

    def __init__(self, code: str) -> None:
        if not isinstance(code, str):
            raise InvalidAccountCodeError("Account code must be a string")
        code = code.strip()
        # TT99/TT200 accepted formats
        import re as _re
        pattern_10 = r"^[1-9]\d{2}\d{3}\d{3}$"  # 10 digits, first 1-9
        pattern_grouped = r"^[1-9]\d{2}\d{3}\d{3}-\d{1,3}$"  # 10+group
        if not (_re.match(pattern_10, code) or _re.match(pattern_grouped, code)):
            raise InvalidAccountCodeError(
                f"Account code must match ^\d{{10}}$ or ^\d{{10}}-{{3}}$; received: {code}"
            )
        self.value = code


class AccountTagMapping:
    """Maps account tag to financial report line per Circular 99 Appendix IV."""

    def __init__(self, tag: AccountTag, report_line_code: str, description: str = "") -> None:
        self.tag = tag
        self.report_line_code = report_line_code
        self.description = description


# ── Entity: Account ──────────────────────────────────────────────────

class Account:
    """Chart of Accounts account aggregate root.

    Invariant checks (all in __post_init__):
    - code valid per AccountCode
    - code unique per company (enforced by repo)
    - category in AccountCategory enum
    - vat_rate in {0, 5, 8, 10} (Decimal); default per enterprise regime
    - at least 1 account_tag (mandatory or custom)
    - report_line per Appendix IV if category ≠ UNDISTRIBUTED_PROFIT
    - system accounts (pre-loaded TT99/TT200) are read-only; modifiable only via migration
    """

    __slots__ = (
        "id",
        "code",
        "name",
        "category",
        "status",
        "vat_rate",
        "account_tags",       # frozenset[AccountTag]
        "report_line",       # str | None (Appendix IV code)
        "parent_id",         # UUID | None (self-referencing sub-account)
        "company_id",        # UUID
        "created_by",        # UUID (must be CHIEF_ACCOUNTANT or admin)
        "created_at",        # datetime (UTC, immutable after set)
        "updated_at",        # datetime (UTC, auto-now on update)
        "audit_checksum",    # str SHA-256 of change event
    )

    def __init__(
        self,
        code: str,
        name: str,
        category: AccountCategory,
        company_id: UUID,
        created_by: UUID,
        vat_rate: float = 0.0,
        report_line: str | None = None,
        parent_id: UUID | None = None,
        account_tags: list[AccountTag] | None = None,
    ) -> None:
        # 1. Validate and store code
        self.code = AccountCode(code).value

        # 2. Basic attrs
        self.name = name.strip()
        self.category = category
        self.company_id = company_id
        self.parent_id = parent_id

        # 3. Status: newly created → ACTIVE
        self.status = AccountStatus.ACTIVE

        # 4. VAT rate: must be 0, 5, 8, or 10
        if vat_rate not in (0, 5, 8, 10):
            raise InvalidAccountCodeError(  # reuse; same error class
                f"VAT rate must be 0, 5, 8, or 10; received: {vat_rate}"
            )
        self.vat_rate = vat_rate

        # 5. Report line: mandatory for all categories except UNDISTRIBUTED_PROFIT
        if category != AccountCategory.UNDISTRIBUTED_PROFIT and not report_line:
            raise InvalidAccountCodeError(
                f"Report line (Appendix IV code) is mandatory for category {category.value}; "
                f"received report_line={report_line}"
            )
        self.report_line = report_line

        # 6. Account tags: at least 1; system adds mandatory tags if none provided
        if account_tags is None:
            account_tags = [AccountTag.REVENUE]  # default; enterprise configures real tags
        elif not any(isinstance(t, AccountTag) for t in account_tags):
            raise InvalidAccountCodeError("At least 1 account tag must be AccountTag enum value")
        # Filter to valid enum values only; deduplicate
        valid_tags = list(dict.fromkeys([t for t in account_tags if isinstance(t, AccountTag)]))
        if not valid_tags:
            raise InvalidAccountCodeError("At least 1 valid account tag required")
        self.account_tags = frozenset(valid_tags)

        # 7. Auditing
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.audit_checksum = self._compute_checksum("create")

        # 8. Post-init invariant
        self._validate_invariant()

    # ── Invariant ──────────────────────────────────────────────────

    def _validate_invariant(self) -> None:
        """Run after __init__; raises ValueError if any invariant broken."""
        # Code format already validated by AccountCode constructor
        # Category must be valid enum
        if self.category not in AccountCategory:
            raise ValueError(f"Invalid category: {self.category}")
        # Status must be valid
        if self.status not in AccountStatus:
            raise ValueError(f"Invalid status: {self.status}")
        # VAT rate check (already in __init__)
        # At least 1 tag
        if not self.account_tags:
            raise ValueError("Account must have at least 1 tag")
        # Report line: if category ≠ UNDISTRIBUTED_PROFIT, report_line must be set
        if self.category != AccountCategory.UNDISTRIBUTED_PROFIT and not self.report_line:
            raise ValueError(
                f"Category {self.category.value} requires report_line (Appendix IV code)"
            )
        # Parent ID: if set, must be same company_id (enforced by repo, not domain)
        # System accounts (pre-loaded) marked via is_system flag at repo level

    # ── Behavioural Methods ────────────────────────────────────────

    def close(self, actor: UUID, reason: str) -> None:
        """Soft-close account: ACTIVE → CLOSED.

        Prohibited if account has associated voucher lines (enforced by repo/service).
        """
        if self.status != AccountStatus.ACTIVE:
            raise ValueError(f"Cannot close account {self.code}: current status is {self.status.value}")
        self.status = AccountStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("close", actor=actor, reason=reason)

    def reopen(self, actor: UUID, reason: str) -> None:
        """CLOSED → ACTIVE.

        Requires reason; audit logged.
        """
        if self.status != AccountStatus.CLOSED:
            raise ValueError(f"Cannot reopen account {self.code}: current status is {self.status.value}")
        self.status = AccountStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("reopen", actor=actor, reason=reason)

    def modify(
        self,
        *,
        new_code: str | None = None,
        new_name: str | None = None,
        new_category: AccountCategory | None = None,
        new_vat_rate: float | None = None,
        new_report_line: str | None = None,
        actor: UUID,
        reason: str,
    ) -> None:
        """Modify account attributes. Requires CHIEF_ACCOUNTANT; audit logged.

        Code change: system checks uniqueness per company; if duplicate → error.
        Category change: only allowed via migration module.
        """
        # Code change
        if new_code is not None:
            # Validate new code format
            new_code_validated = AccountCode(new_code).value
            # Check uniqueness (enforced by repo; domain raises if duplicate)
            # ... repo layer checks (see §4)
            self.code = new_code_validated
            reason = f"{reason}; code changed from {self.code} to {new_code_validated}"

        # Name change
        if new_name is not None:
            self.name = new_name.strip()
            reason = f"{reason}; name changed from '{self.name}'"

        # Category change — prohibited at domain level; repo must block or route to migration
        if new_category is not None:
            raise SystemAccountModificationError(
                "Category modification requires migration module; contact admin"
            )

        # VAT rate change
        if new_vat_rate is not None:
            if new_vat_rate not in (0, 5, 8, 10):
                raise InvalidAccountCodeError(f"VAT rate must be 0,5,8,10; received {new_vat_rate}")
            self.vat_rate = new_vat_rate
            reason = f"{reason}; VAT rate changed to {new_vat_rate}"

        # Report line change
        if new_report_line is not None:
            self.report_line = new_report_line
            reason = f"{reason}; report_line changed to {new_report_line}"

        # Account tags change (add/remove tags)
        # ... (service-layer logic; domain keeps frozenset)

        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("modify", actor=actor, reason=reason)

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        """SHA-256 checksum chaining — mirrors audit-log module pattern.

        Raw: "|".join([prev_checksum or "", str(self.id), action, str(actor), reason, ts.isoformat()])
        """
        import hashlib, json
        raw_parts = [
            self.audit_checksum,  # prev checksum from prior event
            str(self.id),
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

### 1.2 `src/domain/entities/coa.py` — Supporting Entities

- `AccountCategory` enum (9 values) — referenced in FR-02, FR-11
- `AccountStatus` enum (ACTIVE/CLOSED/SUSPENDED) — FR-04
- `AccountTag` enum (7 mandatory + custom) — FR-11, FR-12
- `AccountCode` value object — FR-02 code format validation
- `AccountTagMapping` — FR-13 report line tagging

### 1.3 Domain Exceptions (src/domain/exceptions/coa.py — new file or extend existing)

```python
class CoaError(DomainException):  # extend existing DomainException
    """Base for all COA exceptions."""
    pass

class InvalidAccountCodeError(CoaError):
    """Account code format invalid, or VAT rate out of range, or tag missing."""
    pass

class AccountCodeAlreadyExistsError(CoaError):
    """Code already exists per company_id."""
    pass

class SystemAccountModificationError(CoaError):
    """Attempt to modify system (pre-loaded TT99/TT200) account via normal API."""
    pass

class RequiresChiefAccountantError(CoaError):
    """Operation requires CHIEF_ACCOUNTANT role."""
    pass

class AccountHasVoucherHistoryError(CoaError):
    """Cannot close/delete account with existing voucher references."""
    pass
```

---

## 2. Repository Ports (application/ports/__init__.py)

Add to existing `application/ports/__init__.py`:

```python
# ── Chart of Accounts ────────────────────────────────────────────────

class AccountRepositoryPort(ABC):
    """Port for Chart of Accounts master data (specs-coa-module-2026.md §4.1)."""

    @abstractmethod
    def get_by_id(self, account_id: UUID) -> Account | None:
        pass

    @abstractmethod
    def get_by_code(self, code: str, company_id: UUID) -> Account | None:
        """Return account if code matches format AND belongs to company."""
        pass

    @abstractmethod
    def list_by_company(
        self,
        company_id: UUID,
        *,
        category: AccountCategory | None = None,
        status: AccountStatus | None = None,
        tag: AccountTag | None = None,
        VAT_rate: float | None = None,
    ) -> list[Account]:
        """Paginated list; default order: code asc."""

    @abstractmethod
    def create(self, account: Account) -> Account:
        """Validate invariants; assign new UUID id; persist; return domain entity."""
        pass

    @abstractmethod
    def update(self, account: Account) -> Account:
        """Validate invariants (code uniqueness, vat_rate, tags); append audit event."""
        pass

    @abstractmethod
    def soft_delete(self, account_id: UUID, actor: UUID, reason: str) -> None:
        """Set status=CLOSED; do NOT delete row (audit retention 10yr)."""
        pass

    @abstractmethod
    def list_system_categories(self) -> list[AccountCategory]:
        """Return the 9 system-defined categories (pre-loaded TT99/TT200)."""
        pass

    @abstractmethod
    def list_mandatory_tags(self) -> list[AccountTag]:
        """Return the 7 mandatory AccountTag values."""
        pass


class AccountCategoryRepositoryPort(ABC):
    """Port for account category master data."""

    @abstractmethod
    def get_system_categories(self) -> list[AccountCategory]: ...


class AccountTagRepositoryPort(ABC):
    """Port for account tag master data."""

    @abstractmethod
    def list_mandatory_tags(self) -> list[AccountTag]: ...

    @abstractmethod
    def list_by_company(self, company_id: UUID) -> list[AccountTag]: ...
```

---

## 3. Repository Adapters (infrastructure/repositories/)

### 3.1 `src/infrastructure/repositories/coa_repo.py`

```python
"""SQLAlchemy adapters for Chart of Accounts (specs-coa-module-2026.md §4.2)."""

from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload

from src.application.ports import (
    AccountRepositoryPort,
    AccountCategoryRepositoryPort,
    AccountTagRepositoryPort,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import Base, AccountModel, AccountCategoryModel, AccountTagModel
from src.domain.entities.coa import (
    Account,
    AccountCode,
    AccountCategory,
    AccountStatus,
    AccountTag,
    AccountTagMapping,
)


# ── Models (SQLAlchemy) ──────────────────────────────────────────────

class AccountModel(Base):
    __tablename__ = "accounts"

    id = db.Column(db.UUID, primary_key=True, default=uuid4)
    code = db.Column(db.String(20), nullable=False, unique=False)  # unique per company below
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(
        db.Enum(AccountCategory, native_enum=False, name="account_category_enum"),
        nullable=False,
    )
    status = db.Column(
        db.Enum(AccountStatus, native_enum=False, name="account_status_enum"),
        nullable=False,
        default=AccountStatus.ACTIVE.value,
    )
    vat_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)  # 0, 5, 8, 10
    report_line = db.Column(db.String(20))  # Appendix IV code; nullable for UNDISTRIBUTED_PROFIT
    parent_id = db.Column(db.UUID, db.ForeignKey("accounts.id"), nullable=True)
    company_id = db.Column(db.UUID, db.ForeignKey("companies.id"), nullable=False)
    created_by = db.Column(db.UUID, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=True,
        onupdate=func.now()
    )
    audit_checksum = db.Column(db.String(64), nullable=False)  # SHA-256

    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_accounts_company_code"),
        db.Index("ix_accounts_company_category", "company_id", "category"),
        db.Index("ix_accounts_company_status", "company_id", "status"),
    )

    # Self-referencing relationship (sub-accounts)
    parent = db.relationship(
        "AccountModel",
        remote_side=[id],
        backref="children",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Many-to-one to company (defined in models.py companies table)
    # many-to-many to tags handled via join table account_tag_xref


class AccountCategoryModel(Base):
    __tablename__ = "account_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Asset"
    code_prefix = db.Column(db.String(10), nullable=True)  # e.g., "1."
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_system = db.Column(db.Boolean, nullable=False, default=True)  # pre-loaded system categories


class AccountTagModel(Base):
    __tablename__ = "account_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Revenue"
    code = db.Column(db.String(10), nullable=False, unique=True)  # e.g., "REV"
    is_mandatory = db.Column(db.Boolean, nullable=False, default=True)
    report_line_code = db.Column(db.String(20), nullable=True)  # Appendix IV
    company_id = db.Column(db.UUID, db.ForeignKey("companies.id"), nullable=True)  # NULL = global


# ── Join table for many-to-many Account ↔ Tag (if needed) ────────────
account_tag_xref = db.Table(
    "account_tag_xref",
    db.Column("account_id", db.UUID, db.ForeignKey("accounts.id"), nullable=False),
    db.Column("tag_id", db.Integer, db.ForeignKey("account_tags.id"), nullable=False),
    db.Column("assigned_at", db.DateTime(timezone=True), server_default=func.now()),
)


# ── Repo: Account ──────────────────────────────────────────────────

class SQLAlchemyAccountRepository(AccountRepositoryPort):
    """SQLAlchemy adapter implementing AccountRepositoryPort."""

    def get_by_id(self, account_id: UUID) -> Account | None:
        stmt = select(AccountModel).where(AccountModel.id == account_id)
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_code(self, code: str, company_id: UUID) -> Account | None:
        # Validate code format first (AccountCode value object)
        try:
            validated = AccountCode(code).value
        except InvalidAccountCodeError:
            return None
        stmt = select(AccountModel).where(
            AccountModel.code == validated,
            AccountModel.company_id == company_id,
        )
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self,
        company_id: UUID,
        *,
        category: AccountCategory | None = None,
        status: AccountStatus | None = None,
        tag: AccountTag | None = None,
        VAT_rate: float | None = None,
    ) -> list[Account]:
        stmt = select(AccountModel).where(AccountModel.company_id == company_id)
        if category is not None:
            stmt = stmt.where(AccountModel.category == category)
        if status is not None:
            stmt = stmt.where(AccountModel.status == status)
        if VAT_rate is not None:
            stmt = stmt.where(AccountModel.vat_rate == VAT_rate)
        # Tag filtering via join (simplified: check xref)
        if tag is not None:
            stmt = stmt.select_from(AccountModel).join(
                account_tag_xref, AccountModel.id == account_tag_xref.c.account_id
            ).where(account_tag_xref.c.tag_id == tag.id)  # simplified
        stmt = stmt.order_by(AccountModel.code.asc())
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def create(self, account: Account) -> Account:
        """Persist new Account; validate code uniqueness first."""
        # Check uniqueness
        existing = db.session.scalar(
            select(AccountModel).where(
                AccountModel.code == account.code,
                AccountModel.company_id == account.company_id,
            )
        )
        if existing is not None:
            raise AccountCodeAlreadyExistsError(
                f"Account code {account.code} already exists for company {account.company_id}"
            )
        # Convert domain → model
        model = self._domain_to_model(account)
        db.session.add(model)
        db.session.flush()  # assign id; no commit (caller commits)
        # Return domain entity (freshly loaded or from model)
        return self._model_to_domain(model)

    def update(self, account: Account) -> Account:
        """Update existing account; validate invariants; append audit event."""
        # Fetch current model
        model = db.session.get(AccountModel, account.id)
        if model is None:
            raise ValueError(f"Account {account.id} not found in DB")

        # Check code uniqueness if code changed
        if model.code != account.code:
            existing = db.session.scalar(
                select(AccountModel).where(
                    AccountModel.code == account.code,
                    AccountModel.company_id == account.company_id,
                    AccountModel.id != account.id,  # exclude self
                )
            )
            if existing is not None:
                raise AccountCodeAlreadyExistsError(
                    f"New code {account.code} already exists for company"
                )
            model.code = account.code

        # Update other fields (name, vat_rate, report_line, tags via xref)
        model.name = account.name
        model.vat_rate = account.vat_rate
        model.report_line = account.report_line
        # Tags: delete existing xref rows, insert new ones
        db.session.execute(delete(account_tag_xref).where(account_tag_xref.c.account_id == account.id))
        for tag in account.account_tags:
            # ensure tag exists in tag table; create if not (or require pre-seeded)
            tag_model = db.session.scalar(
                select(AccountTagModel).where(AccountTagModel.name == tag.value)
            )
            if tag_model is None:
                tag_model = AccountTagModel(
                    name=tag.value, code=tag.code, is_mandatory=False,
                    report_line_code=tag.value  # simplify
                )
                db.session.add(tag_model)
            db.session.execute(
                account_tag_xref.insert().values(account_id=account.id, tag_id=tag_model.id)
            )

        model.updated_at = datetime.now(timezone.utc)
        # Append audit event via checksum chain (service layer typically handles this,
        # but repo can auto-set based on changed fields)
        model.audit_checksum = self._compute_checksum("update", actor=account.updated_by, reason="COA update via API")
        db.session.flush()
        return self._model_to_domain(model)

    def soft_delete(self, account_id: UUID, actor: UUID, reason: str) -> None:
        """Set status=CLOSED; do NOT row-delete."""
        model = db.session.get(AccountModel, account_id)
        if model is None:
            raise ValueError(f"Account {account_id} not found")
        if model.status == AccountStatus.ACTIVE:
            # Check for associated voucher lines (simplified: check voucher_lines count)
            # In production: query VoucherModel where account_code = model.code
            # For now, assume check done by service layer
            model.status = AccountStatus.CLOSED
            model.updated_at = datetime.now(timezone.utc)
            model.audit_checksum = self._compute_checksum("soft_delete", actor=actor, reason=reason)
            db.session.flush()

    def _model_to_domain(self, model: AccountModel) -> Account:
        """Convert SQLAlchemy model → domain entity (NO Flask/SQLAlchemy imports in result)."""
        from src.domain.entities.coa import Account, AccountCode, AccountTag  # local import

        # Parse code back (simple; full validation optional)
        code_value = model.code

        # Build account_tags from xref
        tags_set = set()
        # (query xref for this account_id → tag_ids → tag_models → AccountTag enums)
        # Simplified: assume tags pre-seeded; in production, load from xref

        # Determine report_line: if category is UNDISTRIBUTED_PROFIT, may be None
        report_line = model.report_line  # may be None

        account = Account(
            code=code_value,
            name=model.name,
            category=model.category,  # AccountCategory enum
            company_id=model.company_id,
            created_by=model.created_by,
            vat_rate=float(model.vat_rate),
            report_line=report_line,
            account_tags=list(tags_set) if tags_set else [AccountTag.REVENUE],  # default
        )
        # Set id, status, etc. via __init__ parameters; careful with slots.
        # The above __init__ expects many params; we'll use a helper.
        return account  # placeholder; actual implementation builds fully

    def _domain_to_model(self, account: Account) -> AccountModel:
        """Convert domain entity → SQLAlchemy model.

        Must mirror all fields; ensure code format validated (AccountCode).
        """
        from src.domain.entities.coa import AccountCode

        code_validated = AccountCode(account.code).value

        model = AccountModel(
            id=account.id,  # domain entity has id; but model uses default uuid4 — careful
            code=code_validated,
            name=account.name,
            category=account.category,
            status=account.status,
            vat_rate=account.vat_rate,
            report_line=account.report_line,
            parent_id=account.parent_id,
            company_id=account.company_id,
            created_by=account.created_by,
            created_at=account.created_at,
            updated_at=account.updated_at,
            audit_checksum=account.audit_checksum,
        )
        return model

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        import hashlib
        raw_parts = [
            self.audit_checksum if hasattr(self, "audit_checksum") else "",
            str(account.id) if account else "",
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Repo: AccountCategory ──────────────────────────────────────────

class SQLAlchemyAccountCategoryRepository(AccountCategoryRepositoryPort):
    def get_system_categories(self) -> list[AccountCategory]:
        stmt = select(AccountCategoryModel).where(AccountCategoryModel.is_system == True).order_by(AccountCategoryModel.order_index)
        models = db.session.scalars(stmt).all()
        return [AccountCategory(m.name) for m in models]


# ── Repo: AccountTag ───────────────────────────────────────────────

class SQLAlchemyAccountTagRepository(AccountTagRepositoryPort):
    def list_mandatory_tags(self) -> list[AccountTag]:
        stmt = select(AccountTagModel).where(AccountTagModel.is_mandatory == True).order_by(AccountTagModel.code)
        models = db.session.scalars(stmt).all()
        return [AccountTag(m.code) for m in models]  # AccountTag enum values

    def list_by_company(self, company_id: UUID) -> list[AccountTag]:
        stmt = select(AccountTagModel).where(
            or_(AccountTagModel.is_mandatory == True, AccountTagModel.company_id == company_id)
        )
        models = db.session.scalars(stmt).all()
        return [AccountTag(m.code) for m in models]
```

### 3.2 `src/infrastructure/database/models.py` — Add model imports

Add `AccountModel`, `AccountCategoryModel`, `AccountTagModel`, and `account_tag_xref` to the existing models file. Ensure `lazy="selectin"` on relationships (per codebase convention). Add `UniqueConstraint("company_id", "code")` on `AccountModel`.

### 3.3 Migration: `migrations/versions/xxxxx_add_coa_tables.py`

Create manual migration (Alembic-style or Flask-Migrate) creating:
- `accounts` table (columns as in `AccountModel`)
- `account_categories` table (9 system rows inserted)
- `account_tags` table (7 mandatory rows inserted + optional custom)
- `account_tag_xref` join table

Insert initial data:
- 9 `AccountCategory` rows: Asset, Receivable, Inventory, Fixed Asset, Payable, Accrued Expense, Revenue, Operating Expense, Undistributed Profit (with order_index 1-9)
- 7 `AccountTag` rows: Revenue, Tax Payable, Fixed Asset, Inventory, COGS, Operating Expense, Undistributed Profit (is_mandatory=True, report_line_code per Appendix IV)
- Optional: legacy TT200/TT133 mapping rows

Migration ID: auto-generated by `flask db migrate` after adding model files.

---

## 4. Service Layer (application/services/)

### 4.1 `src/application/services/coa_service.py`

```python
"""Chart of Accounts application service (specs-coa-module-2026.md §5)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.application.ports import (
    AccountRepositoryPort,
    AccountCategoryRepositoryPort,
    AccountTagRepositoryPort,
)
from src.domain.entities.coa import (
    Account,
    AccountCategory,
    AccountStatus,
    AccountTag,
    AccountCode,
)
from src.domain.exceptions import (
    InvalidAccountCodeError,
    AccountCodeAlreadyExistsError,
    SystemAccountModificationError,
    RequiresChiefAccountantError,
    AccountHasVoucherHistoryError,
)
from src.infrastructure.database import db


class CoaService:
    """Enforces COA business rules; no Flask/SQLAlchemy imports."""

    def __init__(
        self,
        account_repo: AccountRepositoryPort,
        cat_repo: AccountCategoryRepositoryPort,
        tag_repo: AccountTagRepositoryPort,
    ) -> None:
        self._acc_repo = account_repo
        self._cat_repo = cat_repo
        self._tag_repo = tag_repo

    # ── Creation ──────────────────────────────────────────────────

    def create_account(
        self,
        code: str,
        name: str,
        category: AccountCategory,
        company_id: UUID,
        actor: UUID,  # must be CHIEF_ACCOUNTANT or admin
        vat_rate: float = 0.0,
        report_line: str | None = None,
        account_tags: list[AccountTag] | None = None,
    ) -> Account:
        """Create new account with full invariant validation."""
        # Role check (caller ensures; service asserts as defense-in-depth)
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required on mutations (D11)")

        # Validate code format (AccountCode VO)
        try:
            AccountCode(code)  # raises InvalidAccountCodeError if bad
        except InvalidAccountCodeError as e:
            raise InvalidAccountCodeError(f"Invalid account code: {e}") from e

        # Check code uniqueness per company
        existing = self._acc_repo.get_by_code(code, company_id)
        if existing is not None:
            raise AccountCodeAlreadyExistsError(
                f"Account code {code} already exists for company {company_id}"
            )

        # Validate category is valid enum
        if category not in AccountCategory:
            raise InvalidAccountCodeError(f"Invalid category: {category}")

        # Validate at least 1 tag if provided
        if account_tags is not None and len(account_tags) == 0:
            raise InvalidAccountCodeError("At least 1 account tag required")

        # Build domain entity
        account = Account(
            code=code,
            name=name,
            category=category,
            company_id=company_id,
            created_by=actor,
            vat_rate=vat_rate,
            report_line=report_line,
            account_tags=account_tags,
        )

        # Persist via repo (repo handles DB session; service just orchestrates)
        created = self._acc_repo.create(account)
        db.session.flush()  # ensure persistence; caller commits per pattern (currency_repo pattern)
        return created

    # ── Modification ──────────────────────────────────────────────

    def update_account(
        self,
        account_id: UUID,
        *,
        new_code: str | None = None,
        new_name: str | None = None,
        new_category: AccountCategory | None = None,
        new_vat_rate: float | None = None,
        new_report_line: str | None = None,
        actor: UUID,
        reason: str,
    ) -> Account:
        """Modify account; requires CHIEF_ACCOUNTANT; audit logged.

        Category change prohibited at domain level — repo must block or route to migration.
        """
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required")

        # Fetch current account
        account = self._acc_repo.get_by_id(account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        # Prohibit category change at domain; repo blocks
        if new_category is not None:
            raise SystemAccountModificationError(
                "Category modification requires migration module; contact admin"
            )

        # Apply allowed modifications via domain method
        try:
            account.modify(
                new_code=new_code,
                new_name=new_name,
                new_vat_rate=new_vat_rate,
                new_report_line=new_report_line,
                actor=actor,
                reason=reason,
            )
        except (InvalidAccountCodeError, SystemAccountModificationError) as e:
            raise e

        # Persist
        updated = self._acc_repo.update(account)
        db.session.flush()
        return updated

    # ── Close/Reopen ──────────────────────────────────────────────

    def close_account(self, account_id: UUID, actor: UUID, reason: str) -> Account:
        """Soft-close account: ACTIVE → CLOSED.

        Prohibited if account has voucher history (check at repo/service).
        """
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required")

        account = self._acc_repo.get_by_id(account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        # Check for associated voucher lines (simplified: repo queries voucher count)
        # In production: `has_vouchers = self._acc_repo.has_voucher_history(account_id)`
        # For now, assume service-level guard or allow close; repo will reject if violated
        closed = self._acc_repo.soft_delete(account_id, actor=actor, reason=reason)
        db.session.flush()
        return closed

    def reopen_account(self, account_id: UUID, actor: UUID, reason: str) -> Account:
        """CLOSED → ACTIVE."""
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required")

        account = self._acc_repo.get_by_id(account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")
        if account.status != AccountStatus.CLOSED:
            raise ValueError(f"Account {account.code} is not closed; current status: {account.status.value}")

        reopened = self._acc_repo.soft_delete(account_id, actor=actor, reason=reason)  # reuse soft-delete with reason "reopen"
        # Actually better to have separate repo method reopen_account
        # For brevity: reuse soft_delete with reason "reopen"
        db.session.flush()
        return account  # simplified

    # ── Listing & Search ──────────────────────────────────────────

    def list_by_company(
        self,
        company_id: UUID,
        *,
        category: AccountCategory | None = None,
        status: AccountStatus | None = None,
        tag: AccountTag | None = None,
        VAT_rate: float | None = None,
    ) -> list[Account]:
        return self._acc_repo.list_by_company(
            company_id, category=category, status=status, tag=tag, VAT_rate=VAT_rate
        )

    def list_system_categories(self) -> list[AccountCategory]:
        return self._cat_repo.get_system_categories()

    def list_mandatory_tags(self) -> list[AccountTag]:
        return self._tag_repo.list_mandatory_tags()

    # ── Import / Export ───────────────────────────────────────────

    def import_coa_from_template(self, template_data: list[dict], actor: UUID) -> import_summary:
        """Import COA from TT99 or TT200 XML/JSON template.

        Each dict expected keys: code, name, category (as string), vat_rate, report_line, tags (list of str).
        System:
        - Validates code format
        - Checks uniqueness per company
        - Maps category string → AccountCategory enum
        - Creates accounts; skips duplicates with log
        - Appends audit event per account created/skipped
        - Returns summary: created_count, skipped_count, errors
        """
        from src.domain.entities.coa import AccountCategory  # local import

        created = 0
        skipped = 0
        errors = []

        for row in template_data:
            try:
                code = row.get("code", "")
                name = row.get("name", "")
                cat_str = row.get("category", "")
                vat_rate = float(row.get("vat_rate", 0))
                report_line = row.get("report_line", None)
                tags_str = row.get("tags", [])
                # Map category string to enum
                try:
                    category = AccountCategory(cat_str)
                except ValueError:
                    errors.append(f"Row code={code}: invalid category '{cat_str}'")
                    skipped += 1
                    continue

                # Build tags list from str list
                tags = [AccountTag(t) for t in tags_str]  # may raise if invalid

                # Create account via service method
                self.create_account(
                    code=code,
                    name=name,
                    category=category,
                    company_id=row.get("company_id"),  # from context or row
                    actor=actor,
                    vat_rate=vat_rate,
                    report_line=report_line,
                    account_tags=tags,
                )
                created += 1
            except AccountCodeAlreadyExistsError as e:
                errors.append(str(e))
                skipped += 1
            except InvalidAccountCodeError as e:
                errors.append(f"code={row.get('code')}: {e}")
                skipped += 1
            except Exception as e:
                errors.append(f"code={code}: unexpected error {e}")
                skipped += 1

        return {"created": created, "skipped": skipped, "errors": errors}

    def export_coa_snapshot(self) -> dict:
        """Return current COA snapshot: all accounts with full detail.

        Used for backup, migration, audit.
        """
        accounts = self._acc_repo.list_by_company(company_id="__all__")  # simplified; in prod, per-company
        # Build dict; omit sensitive audit fields or include per policy
        return {
            "version": "v1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "accounts": [
                {
                    "code": a.code,
                    "name": a.name,
                    "category": a.category.value,
                    "status": a.status.value,
                    "vat_rate": a.vat_rate,
                    "report_line": a.report_line,
                    "tags": [t.value for t in a.account_tags],
                }
                for a in accounts
            ],
        }
```

### 4.2 Integration with existing service patterns

- Follow `CurrencyService` pattern: NO Flask/SQLAlchemy imports in service
- `@casbin_required(*roles)` on API routes (like `currencies_bp.py`)
- `assert actor is not None` narrowing after `_require_actor(data)` (same pattern)
- Service per-request instantiation via `_service()` closure in bp (like currencies_bp)

---

## 5. REST API Blueprint (presentation/api/coa_bp.py)

Follow `currencies_bp.py` pattern; 12-15 endpoints.

```python
"""COA API blueprint — Fiscal Years & Accounting Periods style."""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request
from src.application.services.coa_service import CoaService
from src.application.ports import (
    AccountRepositoryPort,
    AccountCategoryRepositoryPort,
    AccountTagRepositoryPort,
)
from src.infrastructure.database import db
from src.infrastructure.repositories.coa_repo import (
    SQLAlchemyAccountRepository,
    SQLAlchemyAccountCategoryRepository,
    SQLAlchemyAccountTagRepository,
)
from src.presentation.rbac import casbin_required
from src.presentation.serializers import (
    serialize_account,
    serialize_account_category,
    serialize_account_tag,
)
from src.presentation.rbac import READ_ROLES, LOCK_WRITE_ROLES, FY_ADMIN_ROLES

coa_bp = Blueprint("coa", __name__)
logger = logging.getLogger(__name__)

READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
LOCK_WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT")
FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # no AUDITOR

# Service per-request factory (currencies pattern)
_service = None


def _service() -> CoaService:
    global _service
    if _service is None:
        fy_repo = SQLAlchemyAccountRepository()
        cat_repo = SQLAlchemyAccountCategoryRepository()
        lock_repo = SQLAlchemyAccountTagRepository()
        _service = CoaService(fy_repo, cat_repo, lock_repo)
    return _service


def _actor(data: dict) -> UUID | None:
    try:
        return UUID(data["actor"]) if data.get("actor") else None
    except (ValueError, TypeError):
        return None


def _require_actor(data: dict):
    actor = _actor(data)
    if actor is None:
        return None, (jsonify({"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}), 400)
    return actor, None


# ── Accounts ──────────────────────────────────────────────────────────

@coa_bp.get("/v1/coa/accounts")
@casbin_required(*READ_ROLES)
def list_accounts():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        years = _service().list_by_company(UUID(company_id))
        return jsonify({"accounts": [serialize_account(a) for a in years]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("list_accounts failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.post("/v1/coa/accounts")
@casbin_required(*AUTO_SEED_ROLES)  # no AUDITOR; write operation
def create_account():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        coa = _service().create_account(
            code=data.get("code", ""),
            name=data.get("name", ""),
            category=AccountCategory(data.get("category")),  # enum validation
            company_id=UUID(data["company_id"]),
            actor=actor,
            vat_rate=float(data.get("vat_rate", 0)),
            report_line=data.get("report_line"),
            account_tags=[AccountTag(t) for t in data.get("tags", [])],
        )
        return jsonify({"account": serialize_account(coa)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except InvalidAccountCodeError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except (AccountCodeAlreadyExistsError, SystemAccountModificationError) as e:
        return jsonify({"error": str(e), "code": "COA_ERROR"}), 409
    except Exception as exc:
        logger.exception("create_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.get("/v1/coa/accounts/<uuid:account_id>")
@casbin_required(*READ_ROLES)
def get_account(account_id: UUID):
    try:
        acct = _service().get_by_id(account_id)
        if acct is None:
            return jsonify({"error": "Account not found", "code": "NOT_FOUND"}), 404
        return jsonify({"account": serialize_account(acct)})
    except Exception as exc:
        logger.exception("get_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.patch("/v1/coa/accounts/<uuid:account_id>")
@casbin_required(*FY_ADMIN_ROLES)  # CHIEF_ACCOUNTANT/ADMIN/DIRECTOR only
def update_account(account_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        acct = _service().update_account(
            account_id=account_id,
            new_code=data.get("code"),
            new_name=data.get("name"),
            new_category=data.get("category"),
            new_vat_rate=float(data.get("vat_rate", 0)) if data.get("vat_rate") else None,
            new_report_line=data.get("report_line"),
            actor=actor,
            reason=data.get("reason", ""),  # mandatory for any COA change
        )
        return jsonify({"account": serialize_account(acct)})
    except (InvalidAccountCodeError, SystemAccountModificationError, AccountCodeAlreadyExistsError) as e:
        return jsonify({"error": str(e), "code": e.code if hasattr(e, "code") else "COA_ERROR"}), 409 if isinstance(e, AccountCodeAlreadyExistsError) else 422
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("update_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.post("/v1/coa/accounts/<uuid:account_id>/close")
@casbin_required("CHIEF_ACCOUNTANT")
def close_account(account_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        acct = _service().close_account(account_id, actor=actor, reason=data.get("reason", ""))
        return jsonify({"account": serialize_account(acct)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except AccountHasVoucherHistoryError as e:
        return jsonify({"error": str(e), "code": "COA_HAS_VOUCHER_HISTORY"}), 409
    except Exception as exc:
        logger.exception("close_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── System categories & tags ────────────────────────────────────────

@coa_bp.get("/v1/coa/categories")
@casbin_required(*READ_ROLES)
def list_categories():
    cats = _service().list_system_categories()
    return jsonify({"categories": [c.value for c in cats]})


@coa_bp.get("/v1/coa/tags/mandatory")
@casbin_required(*READ_ROLES)
def list_mandatory_tags():
    tags = _service().list_mandatory_tags()
    return jsonify({"tags": [t.value for t in tags]})


# ── Import/Export ──────────────────────────────────────────────────

@coa_bp.post("/v1/coa/import")
@casbin_required(*FY_ADMIN_ROLES)
def import_coa():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        summary = _service().import_coa_from_template(data.get("template_rows", []), actor)
        return jsonify({"import_summary": summary})
    except Exception as exc:
        logger.exception("import_coa failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.get("/v1/coa/export")
@casbin_required(*READ_ROLES)
def export_coa():
    try:
        snapshot = _service().export_coa_snapshot()
        return jsonify(snapshot)
    except Exception as exc:
        logger.exception("export_coa failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
```

### 5.1 Serializers (src/presentation/serializers/coa.py or extend `__init__.py`)

Add to `src/presentation/serializers/__init__.py`:

```python
def serialize_account(account) -> dict:
    return {
        "id": str(account.id),
        "code": account.code,
        "name": account.name,
        "category": account.category.value,
        "status": account.status.value,
        "vat_rate": account.vat_rate,
        "report_line": account.report_line,
        "tags": [t.value for t in account.account_tags],
        "created_by": str(account.created_by) if account.created_by else None,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }


def serialize_account_category(cat) -> dict:
    return {"id": None, "name": cat.value, "code_prefix": None, "is_system": True}


def serialize_account_tag(tag) -> dict:
    return {"id": None, "name": tag.value, "code": tag.code, "is_mandatory": True}
```

---

## 6. Database Migration (manual `flask db migrate`)

Migration file: `migrations/versions/a1b2c3d4e5f6_add_coa_tables.py`

```python
"""Add Chart of Accounts tables (Circular 99 compliance).

Migration ID: auto by flask db migrate after adding model files.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "previous_revision_id"  # e.g., the last fiscal-year migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create account_categories table (9 system rows)
    op.create_table(
        "account_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("code_prefix", sa.String(10), nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, default=0),
        sa.Column("is_system", sa.Boolean, nullable=False, default=True),
    )
    # Insert 9 system categories
    categories = [
        ("Asset", "1.", 1, True),
        ("Receivable", "2.", 2, True),
        ("Inventory", "3.", 3, True),
        ("Fixed Asset", "4.", 4, True),
        ("Payable", "5.", 5, True),
        ("Accrued Expense", "6.", 6, True),
        ("Revenue", "7.", 7, True),
        ("Operating Expense", "8.", 8, True),
        ("Undistributed Profit", "9.", 9, True),
    ]
    for name, prefix, idx, sys_flag in categories:
        op.execute(
            f"INSERT INTO account_categories (name, code_prefix, order_index, is_system) "
            f"VALUES ('{name}', '{prefix}', {idx}, {sys_flag})"
        )

    # 2. Create account_tags table (7 mandatory + capacity for custom)
    op.create_table(
        "account_tags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, default=True),
        sa.Column("report_line_code", sa.String(20), nullable=True),
        sa.Column("company_id", sa.Uuid, sa.ForeignKey("companies.id"), nullable=True),
    )
    # Insert 7 mandatory tags with Appendix IV report line codes
    tags = [
        ("Revenue", "REV", "1.1", True),     # Appendix IV line for revenue
        ("Tax Payable", "TP", "2.1", True),  # VAT/CIT payable
        ("Fixed Asset", "FA", "3.1", True),  # Tangible fixed assets
        ("Inventory", "IN", "4.1", True),    # Goods for sale, WIP
        ("Cost of Goods Sold", "CO", "5.1", True),  # Cost of goods sold
        ("Operating Expense", "OE", "6.1", True),  # Selling/Admin expenses
        ("Undistributed Profit", "UP", "7.1", True),  # Retained earnings
    ]
    for name, code, report_line, mandatory in tags:
        op.execute(
            f"INSERT INTO account_tags (name, code, is_mandatory, report_line_code) "
            f"VALUES ('{name}', '{code}', {mandatory}, '{report_line}')"
        )

    # 3. Create account_tag_xref join table (many-to-many)
    op.create_table(
        "account_tag_xref",
        sa.Column("account_id", sa.Uuid, sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("account_tags.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("account_id", "tag_id", name="uq_account_tag_xref"),
    )

    # 4. Create accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid, primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.Enum(
            "Asset", "Receivable", "Inventory", "Fixed Asset",
            "Payable", "Accrued Expense", "Revenue", "Operating Expense",
            "Undistributed Profit",
            name="account_category_enum"
        ), nullable=False),
        sa.Column("status", sa.Enum(
            "Active", "Closed", "Suspended",
            name="account_status_enum"
        ), nullable=False, default="Active"),
        sa.Column("vat_rate", sa.Numeric(5, 2), nullable=False, default=0.00),
        sa.Column("report_line", sa.String(20), nullable=True),
        sa.Column("parent_id", sa.Uuid, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("company_id", sa.Uuid, sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("created_by", sa.Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  onupdate=sa.func.now()),
        sa.Column("audit_checksum", sa.String(64), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_accounts_company_code"),
        sa.Index("ix_accounts_company_category", "company_id", "category"),
        sa.Index("ix_accounts_company_status", "company_id", "status"),
    )

    # 5. Add system categories seed (already done above via op.execute)
    #    Add mandatory tags seed (already done above)


def downgrade() -> None:
    # Drop tables in reverse order (dependencies)
    op.drop_table("accounts")
    op.drop_table("account_tag_xref")
    op.drop_table("account_tags")
    op.drop_table("account_categories")
```

---

## 7. Test Plan (unit + integration)

### 7.1 Unit Tests (`tests/unit/coa/`)

| Test Class | Key Tests |
|---|---|
| `TestAccount` | `__init__` invariant checks: valid/invalid code, category, tags, report_line; `close()`/`reopen()` transitions; `modify()` prohibits category change |
| `TestAccountCode` | `^\d{10}$` and `^\d{10}-\d{3}$` acceptance; `AB12345678` rejection |
| `TestAccountCategory` | 9 enum values; `UNDISTRIBUTED_PROFIT` has no report_line requirement |
| `TestAccountTag` | 7 mandatory + custom; `is_mandatory` flag |
| `TestCoaService` | `create_account` happy path + code-exists error + invalid-code error + tag-req; `close_account` + voucher-history guard; `update_account` category-prohibited |
| `TestCoaServiceImport` | TT99 template import: created/skipped/errors counts; duplicate handling |

### 7.2 Integration Tests (`tests/integration/test_coa_api.py`)

| Test Class | Key Tests |
|---|---|
| `TestCoaAPI` | `list_accounts` with/without company_id 400; `create_account` with AUDITOR → 403 (RBAC); `create_account` missing actor → 400; `update_account` with reason mandatory; `close_account` on account with vouchers → 409; `close_account` on open account → 200; `list_categories`; `list_mandatory_tags`; `import_coa` with TT99 template; `export_coa` |
| `TestCoaRBAC` | Role enforcement: READ_ROLES on read routes; AUTO_SEED_ROLES (no AUDITOR) on write; FY_ADMIN_ROLES on import/close |

### 7.3 Test Data Factories

- `account_factory(code="1001000001", name="Cash", category=Asset, tags=[Revenue])`
- `tt99_template = [..., ...]` (sample rows matching Circular 99 structure)

### 7.4 Test Commands

```bash
# Run COA unit tests
pytest tests/unit/coa/ -q

# Run COA integration tests
pytest tests/integration/test_coa_api.py -q

# Full suite regression
pytest -q  # should remain 262 pass + 2 fail + 14 err baseline (untouched company_api)
```

---

## 8. Non-Functional & Compliance

| Category | Requirement |
|---|---|
| **LSP / mypy** | New files clean; domain entities free of sqlalchemy/web imports; ports use abstract types only |
| **Ruff** | `ruff check src tests` scoped to new files clean; no new errors |
| **Black** | `black --check` on new files clean |
| **Security** | `@casbin_required` on all routes; AUDITOR read-only (excluded from AUTO_SEED_ROLES); actor UUID on all mutations (D11); no plain-text secrets; audit checksums SHA-256 immutable |
| **Performance** | Account lookup by code: ≤50ms (index on company_id+code); list by company: ≤200ms for ≤200 accounts; import of 1000-account TT99 template: ≤5s |
| **Compatibility** | TT99 out-of-box; TT200/TT133 import with mapping; IFRS convergence roadmap (v2.1); existing voucher/invoice modules unchanged (backward-compatible account codes) |
| **Data Retention** | All COA changes audit-logged with SHA-256 chain; 10-year retention per Law on Accounting §21; prior COA versions archived, not deleted |

---

## 9. Migration & Upgrade Path

| Scenario | Action |
|---|---|
| **Fresh deploy** | Run `flask db init; flask db migrate; flask db upgrade` — creates `accounts`, `account_categories`, `account_tags`, `account_tag_xref` tables + seeds 9 categories + 7 mandatory tags |
| **Upgrade from v1 (no COA)** | Migration `a1b2c3d4e5f6_add_coa_tables.py` adds tables; no data migration needed (new install) |
| **Switch from Circular 200 → Circular 99** | Use `import_coa` API endpoint with TT99 template; system maps legacy codes; old accounts remain in DB (read-only, archived version); new accounts created per TT99; audit events link old→new |
| **Revert to legacy** | Not recommended; old account codes retained in history; new TT99 accounts added side-by-side; report generation supports both regimes via version flag |

---

## 10. Integration Checklist (pre-deploy)

- [ ] `flask db migrate + upgrade` runs clean on test sqlite
- [ ] `ruff check src tests` — no new errors (my module scoped)
- [ ] `black --check` on new files clean
- [ ] `mypy src` — no new errors (domain entities clean; infra may have pre-existing LSP noise)
- [ ] Unit tests: `pytest tests/unit/coa/ -q` → all green
- [ ] Integration tests: `pytest tests/integration/test_coa_api.py -q` → all green
- [ ] RBAC test: AUDITOR cannot POST /create_account; gets 403
- [ ] RBAC test: POST /create_account with missing actor → 400
- [ ] Import test: TT99 template rows → accounts created; duplicates skipped with log
- [ ] VAT rate test: only 0/5/8/10 accepted; others rejected 422
- [ ] Tag test: at least 1 tag mandatory; 0 tags → 422
- [ ] Close test: account with voucher history → 409; open account → 200
- [ ] Performance: simple bench (optional)

---

## 11. References & Readings (within this doc)

- `Law on Accounting 2015` (Vietnamese), Chap IV — Chart of Accounts, audit trail, 10-year retention
- `Circular 99/2025/TT-BTC` — effective 01/01/2026; replaces Circular 200; principle-based COA; Appendix IV report lines
- `Circular 200/2014/TT-BTC` — legacy; 9 categories, 76 Level-1, 71 Level-2 accounts; code format
- `Circular 133/2016/TT-BTC` — SME simplified COA
- `AGENTS.md` — RBAC, coding conventions, testing strategy; `caveman` mode; Karpathy guidelines
- `docs/CODING_CONVENTION.md` — naming, layer boundaries, commit format: `type(scope): description`
- `docs/TESTING_STRATEGY.md` — test levels; no UI-level tests for pure logic; factory-driven isolated state; no coverage-chasing
- `karpathy-guidelines` skill — behavioral guidelines for reduced mistakes
- Existing module patterns: `currencies_bp.py` (service per-request, test-engine hook); `fiscal_year_bp.py` (9 routes, `@casbin_required`); `system_settings_bp.py` (broken, adapter missing — out of scope)

---

*End of Technical Specifications*

**Next Step:** Upon specs approval, proceed to:
1. Create `src/domain/entities/coa.py` + `src/domain/exceptions/coa.py` (new or extend existing)
2. Add repository adapters `src/infrastructure/repositories/coa_repo.py` + model additions to `models.py`
3. Create manual migration `migrations/versions/a1b2c3d4e5f6_add_coa_tables.py`
4. Create `src/application/services/coa_service.py`
5. Create `src/presentation/api/coa_bp.py` + serializers
6. Create unit + integration test files
7. Run full suite regression; ensure 262 pass baseline preserved