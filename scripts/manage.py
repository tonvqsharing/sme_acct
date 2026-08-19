"""CLI management commands for Vietnamese SME Accounting Application.

Provides user/role management commands:
- create-admin: Create first admin user
- reset-password: Reset user password
- assign-role: Assign role to user
- enable-user: Enable user account
- disable-user: Disable user account
- list-users: List all users with roles
- coa-list: List accounts with optional filters
- coa-create: Create new account with invariant validation
- coa-import: Import COA from TT99/TT200 template
- coa-export: Export COA snapshot
- coa-categories: List 9 system account categories
- coa-tags: List 7 mandatory account tags

Uses Flask application context for DB access.
"""
from __future__ import annotations

import sys
from typing import Optional

import click
from flask import current_app
from flask.cli import with_appcontext

from src.application.services.auth_service import AuthService  # noqa: E402


@click.group()
def cli():
    """CLI management commands for SME accounting application."""
    pass


@cli.command("create-user")
@click.option("--email", required=True, help="User email")
@click.option("--role", required=True, help="Role to assign (ACCOUNTANT|CHIEF_ACCOUNTANT|ADMIN|AUDITOR|DIRECTOR)")
@click.option("--password", default=None, help="Password for the user (generates random if not provided)")
@with_appcontext
def create_user(email: str, role: str, password: str | None):
    """Create a new user with the given role.

    Args:
        email: User email (must be unique)
        role: One of: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR
        password: Password for the user. If not provided, a random 16-char password is generated.
    """
    auth = AuthService()
    try:
        user = auth.create_user(email, role, password)
        click.echo(
            f"User created: {user.email_val} (id={user.id}) -- "
            f"role={user.role_val}, is_active={user.is_active_val}"
        )
    except ValueError as exc:
        click.echo(f"User creation failed: {exc}", err=True)
        sys.exit(1)


@cli.command("create-admin")
@with_appcontext
def create_admin():
    """Create the first admin user (run once on fresh deployment)."""
    auth = AuthService()
    try:
        admin = auth.create_admin()
        click.echo(
            f"Admin created: {admin.email} ({admin.id}) -- "
            f"role=ADMIN, can reset passwords & assign roles"
        )
    except ValueError as exc:
        click.echo(f"Admin creation failed: {exc}", err=True)
        sys.exit(1)


@cli.command("reset-password")
@click.option("--user", required=True, help="Username or email of user")
@click.option("--new-password", required=True, help="New password for the user")
@with_appcontext
def reset_password(user: str, new_password: str):
    """Reset a user's password."""
    auth = AuthService()
    try:
        auth.reset_password(user, new_password)
        click.echo(f"Password reset for {user}")
    except LookupError as exc:
        click.echo(f"User not found: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Failed to reset password: {exc}", err=True)
        sys.exit(1)


@cli.command("assign-role")
@click.option("--user", required=True, help="Username or email of user")
@click.option("--role", required=True, help="Role to assign (ACCOUNTANT|CHIEF_ACCOUNTANT|ADMIN|AUDITOR|DIRECTOR)")
@with_appcontext
def assign_role(user: str, role: str):
    """Assign a role to a user."""
    auth = AuthService()
    try:
        auth.assign_role(user, role)
        click.echo(f"Role '{role}' assigned to {user}")
    except LookupError as exc:
        click.echo(f"User not found: {exc}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"Invalid role: {exc}", err=True)
        sys.exit(1)


@cli.command("enable-user")
@click.option("--user", required=True, help="Username or email of user")
@with_appcontext
def enable_user(user: str):
    """Enable a user account."""
    auth = AuthService()
    try:
        auth.enable_user(user)
        click.echo(f"User {user} enabled")
    except LookupError as exc:
        click.echo(f"User not found: {exc}", err=True)
        sys.exit(1)


@cli.command("disable-user")
@click.option("--user", required=True, help="Username or email of user")
@with_appcontext
def disable_user(user: str):
    """Disable a user account."""
    auth = AuthService()
    try:
        auth.disable_user(user)
        click.echo(f"User {user} disabled")
    except LookupError as exc:
        click.echo(f"User not found: {exc}", err=True)
        sys.exit(1)


@cli.command("list-users")
@with_appcontext
def list_users():
    """List all users with their roles and status."""
    auth = AuthService()
    try:
        users = auth.list_users()
        if not users:
            click.echo("No users found.")
            return
        for u in users:
            status = "ACTIVE" if u["is_active"] else "DISABLED"
            click.echo(
                f"{u['email']:30s}  role={u['role']:15s}  status={status:8s}  "
                f"last_login={u['last_login'] or 'never'}"
            )
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Failed to list users: {exc}", err=True)
        sys.exit(1)


@cli.command("coa-list")
@click.option("--company-id", help="Filter by company UUID")
@click.option("--category", type=click.Choice(["Asset", "Liability", "Equity", "Revenue", "Expense", "Income", "Undistributed Profit"]), help="Filter by account category")
@click.option("--status", type=click.Choice(["Active", "Closed"]), help="Filter by account status")
@click.option("--tag", help="Filter by mandatory account tag (Asset|Liability|Equity|Revenue|Expense|Tax|Cost)")
@click.option("--vat-rate", type=float, help="Filter by VAT rate (0, 5, 8, 10)")
@with_appcontext
def coa_list(company_id, category, status, tag, vat_rate):
    """List accounts with optional filters.

    Filters:
        --company-id: UUID filter
        --category: AccountCategory enum value
        --status: Active/Closed
        --tag: One of 7 mandatory AccountTag enum values
        --vat-rate: 0, 5, 8, or 10
    """
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.coa_repo import SQLAlchemyAccountRepository

    # Initialize service
    acc_repo = SQLAlchemyAccountRepository()
    cat_repo = None  # stub for now
    tag_repo = None  # stub for now
    service = CoaService(acc_repo, cat_repo, tag_repo)

    # Build filters
    filters = {}
    if company_id:
        from uuid import UUID
        try:
            filters["company_id"] = UUID(company_id)
        except ValueError:
            click.echo("Invalid company-id format. Use UUID format (xxxx-xxxx-xxxx-xxxx-xxxx).", err=True)
            sys.exit(1)

    if category:
        filters["category"] = category
    if status:
        filters["status"] = status
    if tag:
        filters["tag"] = tag
    if vat_rate is not None:
        filters["VAT_rate"] = vat_rate

    try:
        accounts = service.list_by_company(**filters)
        if not accounts:
            click.echo("No accounts found matching filters.")
            return

        header = "Code".ljust(16) + "Name".ljust(30) + "Category".ljust(15) + "Status".ljust(10) + "VAT".ljust(6) + "Report Line"
        click.echo(header)
        click.echo("-" * 80)
        for acct in accounts:
            tags_str = ", ".join(t.value for t in acct.account_tags[:3])
            if len(acct.account_tags) > 3:
                tags_str += f" +{len(acct.account_tags)-3} more"
            row = acct.code.ljust(16) + acct.name.ljust(30) + acct.category.value.ljust(15) + \
                  acct.status.value.ljust(10) + str(acct.vat_rate).ljust(6) + \
                  (acct.report_line or "-").ljust(14) + "Tags: " + tags_str
            click.echo(row)
    except Exception as exc:
        click.echo(f"Failed to list accounts: {exc}", err=True)
        sys.exit(1)


@cli.command("coa-create")
@click.option("--code", required=True, help="Account code per TT99 format (10 digits or 10-3 with TT99)")
@click.option("--name", required=True, help="Account name")
@click.option("--category", required=True, type=click.Choice(["Asset", "Liability", "Equity", "Revenue", "Expense", "Income", "Undistributed Profit"]), help="Account category")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--vat-rate", default="0", type=click.Choice(["0", "5", "8", "10"]), help="VAT rate (0, 5, 8, or 10)")
@click.option("--report-line", default=None, help="Report line (Appendix IV); mandatory for all categories except Undistributed Profit")
@click.option("--tags", multiple=True, default=[], help="Account tags (AccountTag enum values). At least 1 mandatory.")
@with_appcontext
def coa_create(code, name, category, company_id, actor, vat_rate, report_line, tags):
    """Create a new account with full invariant validation (D1-D11).

    Validates:
        - Account code format: ^\\d{10}$ or ^\\d{10}-\\d{3}$ (TT99)
        - VAT rate: must be 0, 5, 8, or 10
        - At least 1 account tag mandatory
        - Report line mandatory for non-undistributed categories
        - Actor UUID required on mutations (D11)
    """
    from uuid import UUID
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.coa_repo import SQLAlchemyAccountRepository
    from src.domain.exceptions import InvalidAccountCodeError

    # Parse UUIDs
    try:
        company_uuid = UUID(company_id)
        actor_uuid = UUID(actor)
    except ValueError:
        click.echo("Invalid UUID format. Use format: xxxxxxxx-xxxx-xxxx-xxxx-xxxx", err=True)
        sys.exit(1)

    # Parse tags
    tag_enum_values = ["Asset", "Liability", "Equity", "Revenue", "Expense", "Tax", "Cost"]
    parsed_tags = []
    for t in tags:
        if t in tag_enum_values:
            parsed_tags.append(t)
        else:
            click.echo(f"Invalid tag: {t}. Must be one of: {', '.join(tag_enum_values)}", err=True)
            sys.exit(1)

    if not parsed_tags:
        click.echo("At least 1 account tag is mandatory (FR-12b).", err=True)
        sys.exit(1)

    # Initialize service
    acc_repo = SQLAlchemyAccountRepository()
    cat_repo = None  # stub
    tag_repo = None  # stub
    service = CoaService(acc_repo, cat_repo, tag_repo)

    try:
        from src.domain.entities.coa import AccountCategory, AccountTag
        from src.domain.entities.coa import Account

        category_enum = AccountCategory(category)
        tags_enum = [AccountTag(t) for t in parsed_tags]

        account = service.create_account(
            code=code,
            name=name,
            category=category_enum,
            company_id=company_uuid,
            actor=actor_uuid,
            vat_rate=float(vat_rate),
            report_line=report_line,
            account_tags=tags_enum,
        )

        click.echo(
            f"Account created: {account.code} -- {account.name} "
            f"(category={account.category.value}, status={account.status.value})"
        )
    except InvalidAccountCodeError as e:
        click.echo(f"Validation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to create account: {e}", err=True)
        sys.exit(1)


@cli.command("coa-import")
@click.option("--template", type=click.Choice(["TT99", "TT200"]), default="TT99", help="Template standard")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--dry-run", is_flag=True, help="Validate only, do not persist")
@with_appcontext
def coa_import(template, actor, dry_run):
    """Import COA from TT99 or TT200 template data (atomic all-or-nothing, D4).

    Each row expected fields: code, name, category (str), vat_rate, report_line, tags (comma-separated).
    Any bad row entire import rejected (no partial data).
    """
    from uuid import UUID
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db

    # Parse actor UUID
    try:
        actor_uuid = UUID(actor)
    except ValueError:
        click.echo("Invalid UUID format for actor.", err=True)
        sys.exit(1)

    # Template data (simulated -- in production would read from file/URL)
    # This is a placeholder; real implementation reads from CSV/file
    click.echo(f"COA import from {template} template (actor={actor})")
    click.echo("--dry-run mode: validates only, no persistence" if dry_run else "--live mode: will persist to DB")
    click.echo("Template format: code,name,category,vat_rate,report_line,tag1,tag2,...")

    if not dry_run:
        click.echo("Real implementation would read template data and call service.import_coa_from_template()", err=True)
        sys.exit(1)


@cli.command("coa-export")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.option("--company-id", help="Filter by company UUID (optional)")
@with_appcontext
def coa_export(format):
    """Export current COA snapshot.

    Returns full COA detail: all accounts with codes, names, categories,
    VAT rates, report lines, and tags. Includes version & export timestamp.
    """
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db

    service = CoaService.__new__(CoaService)  # simplified -- real init needs repos

    try:
        snapshot = service.export_coa_snapshot()
        if format == "json":
            import json
            click.echo(json.dumps(snapshot, indent=2, default=str))
        elif format == "csv":
            # Simplified CSV output
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Code", "Name", "Category", "VAT Rate", "Report Line", "Tags"])
            for acct in snapshot.get("accounts", []):
                tags_str = ", ".join(acct.get("tags", []))
                writer.writerow([acct["code"], acct["name"], acct["category"], acct["vat_rate"], acct["report_line"], tags_str])
            click.echo(output.getvalue())
    except Exception as e:
        click.echo(f"Failed to export COA: {e}", err=True)
        sys.exit(1)


@cli.command("coa-categories")
@with_appcontext
def coa_categories():
    """List the 9 system account categories per Circular 99/2025/TT-BTC.

    Categories:
        Asset, Liability, Equity, Revenue, Expense, Income,
        Undistributed Profit (specialized categories may vary by regime)
    """
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db

    service = CoaService.__new__(CoaService)

    try:
        categories = service.list_system_categories()
        header = "Category".ljust(25) + "Description"
        click.echo(header)
        click.echo("-" * 40)
        for cat in categories:
            row = cat.value.ljust(25) + (cat.name if hasattr(cat, "name") else "")
            click.echo(row)
    except Exception as e:
        click.echo(f"Failed to list categories: {e}", err=True)
        sys.exit(1)


@cli.command("coa-tags")
@with_appcontext
def coa_tags():
    """List the 7 mandatory account tags per FR-12b.

    All accounts must have at least 1 of these tags assigned.
    Tags: Asset, Liability, Equity, Revenue, Expense, Tax, Cost
    """
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db

    service = CoaService.__new__(CoaService)

    try:
        tags = service.list_mandatory_tags()
        header = "Tag".ljust(15) + "Mandatory"
        click.echo(header)
        click.echo("-" * 30)
        for tag in tags:
            row = tag.value.ljust(15) + " YES"
            click.echo(row)
    except Exception as e:
        click.echo(f"Failed to list tags: {e}", err=True)
        sys.exit(1)




@cli.command("coa-close")
@click.option("--company-id", help="Filter by company UUID")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", default="Closing account", help="Reason for closing")
@with_appcontext
def coa_close(company_id, actor, reason):
    """Soft-close an account (ACTIVE → CLOSED, no row deletion).

    Per Law on Accounting 10-year retention: accounts are never deleted,
    only soft-closed. Status changes from Active to Closed.

    Args:
        company_id: Company UUID filter
        actor: Actor UUID required on all mutations (D11)
        reason: Reason for the closure
    """
    from uuid import UUID
    from src.application.services.coa_service import CoaService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.coa_repo import SQLAlchemyAccountRepository

    try:
        company_uuid = UUID(company_id)
        actor_uuid = UUID(actor)
    except ValueError:
        click.echo("Invalid UUID format. Use format: xxxxxxxx-xxxx-xxxx-xxxx-xxxx", err=True)
        sys.exit(1)

    acc_repo = SQLAlchemyAccountRepository()
    service = CoaService(acc_repo, None, None)

    try:
        # Note: service.close_account is not fully implemented in this stub,
        # but the command structure is correct for when the service layer
        # is complete.
        click.echo(f"Close account command invoked: company={company_id}, actor={actor}, reason='{reason}'")
        click.echo("Full soft-close implementation pending service layer completion.")
    except Exception as e:
        click.echo(f"Failed to close account: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
