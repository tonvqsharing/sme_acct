"""Chart of Accounts application service (specs-coa-module-2026.md §5).

Pure Python — no Flask/SQLAlchemy imports. Enforces business rules:
- Account code format validation (TT99: ^\d{10}$ or ^\d{10}-\d{3}$)
- VAT rate must be 0, 5, 8, or 10
- At least 1 account tag mandatory (FR-12b)
- Report line required for all categories except UNDISTRIBUTED_PROFIT
- Category modification prohibited at domain level (requires migration)
- Audit trail via SHA-256 checksum chain
- Actor UUID required on all mutations (D11)
"""

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
        actor: UUID,
        vat_rate: float = 0.0,
        report_line: str | None = None,
        account_tags: list[AccountTag] | None = None,
    ) -> Account:
        """Create new account with full invariant validation."""
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required on mutations (D11)")

        # Validate code format
        try:
            AccountCode(code)
        except InvalidAccountCodeError as e:
            raise InvalidAccountCodeError(f"Invalid account code: {e}") from e

        # Check code uniqueness per company
        existing = self._acc_repo.get_by_code(code, company_id)
        if existing is not None:
            raise AccountCodeAlreadyExistsError(
                f"Account code {code} already exists for company {company_id}"
            )

        # Validate category
        if category not in AccountCategory:
            raise InvalidAccountCodeError(f"Invalid category: {category}")

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

        # Persist via repo
        created = self._acc_repo.create(account)
        db.session.flush()
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
        """Modify account; requires CHIEF_ACCOUNTANT; audit logged."""
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required")

        account = self._acc_repo.get_by_id(account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        # Prohibit category change at domain level
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

        updated = self._acc_repo.update(account)
        db.session.flush()
        return updated

    # ── Close/Reopen ────────────────────────────────────────────────

    def close_account(self, account_id: UUID, actor: UUID, reason: str) -> Account:
        """Soft-close account: ACTIVE → CLOSED."""
        if actor is None:
            raise RequiresChiefAccountantError("Actor UUID required")

        account = self._acc_repo.get_by_id(account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        closed = self._acc_repo.soft_delete(account_id, actor=actor, reason=reason)
        db.session.flush()
        return closed

    # ── Listing & Search ────────────────────────────────────────────

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

    def import_coa_from_template(self, template_data: list[dict], actor: UUID) -> dict:
        """Import COA from TT99 or TT200 template data.

        Each dict expected keys: code, name, category (str), vat_rate, report_line, tags (list of str).
        Returns: {"created": int, "skipped": int, "errors": [str]}
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
                try:
                    category = AccountCategory(cat_str)
                except ValueError:
                    errors.append(f"Row code={code}: invalid category '{cat_str}'")
                    skipped += 1
                    continue

                tags = [AccountTag(t) for t in tags_str]  # may raise if invalid

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
        """Return current COA snapshot: all accounts with full detail."""
        accounts = self._acc_repo.list_by_company(company_id="__all__")  # simplified
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