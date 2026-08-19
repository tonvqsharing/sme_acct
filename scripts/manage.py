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





@cli.command("fy-list")
@click.option("--company-id", help="Filter by company UUID")
@click.option("--status", type=click.Choice(["OPEN", "CLOSED", "DRAFT", "LOCKED"]), help="Filter by fiscal year status")
@with_appcontext
def fy_list(company_id, status):
    """List fiscal years by company with optional filters.

    Filters:
        --company-id: UUID filter for tenant isolation
        --status: Filter by status (OPEN/CLOSED/DRAFT/LOCKED)
    """
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository

    # Parse company_id UUID if provided
    company_uuid = None
    if company_id:
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            click.echo("Invalid company-id format. Use UUID format (xxxx-xxxx-xxxx-xxxx-xxxx).", err=True)
            sys.exit(1)

    # Initialize service
    fy_repo = SQLAlchemyFiscalYearRepository()
    service = FiscalYearService(fy_repo)

    try:
        years = service.list_by_company(company_id=company_uuid, status_name=status)
        if not years:
            click.echo("No fiscal years found matching filters.")
            return

        header = "ID".ljust(36) + "Name".ljust(25) + "Status".ljust(12) + "Start Date".ljust(14) + "End Date".ljust(14)
        click.echo(header)
        click.echo("-" * 96)
        for fy in years:
            start_str = fy.start_date.strftime("%Y-%m-%d") if fy.start_date else "N/A"
            end_str = fy.end_date.strftime("%Y-%m-%d") if fy.end_date else "N/A"
            active_str = "ACTIVE" if fy.is_active else "INACTIVE"
            row = fy.id.ljust(36) + fy.name.ljust(25) + fy.status.value.ljust(12) + start_str.ljust(14) + end_str.ljust(14) + active_str
            click.echo(row)
    except Exception as exc:
        click.echo(f"Failed to list fiscal years: {exc}", err=True)
        sys.exit(1)





@cli.command("fy-create")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--name", required=True, help="Fiscal year name")
@click.option("--start-month", type=click.IntRange(1, 12), required=True, help="Start month (1-12)")
@click.option("--start-day", type=click.IntRange(1, 28), required=True, help="Start day (1-28)")
@click.option("--period-type", type=click.Choice(["CALENDAR", "FISCAL_APR", "FISCAL_JUL", "FISCAL_OCT"]), required=True, help="Period type: CALENDAR=1, FISCAL_APR=4, FISCAL_JUL=7, FISCAL_OCT=10 (FISCAL_15 rejected per Vietnamese law)")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", required=True, help="Reason for creation (mandatory per D11)")
@with_appcontext
def fy_create(company_id, name, start_month, start_day, period_type, actor, reason):
    """Create a new fiscal year."""
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = UUID(company_id)
        actor_uuid = UUID(actor)
    except ValueError:
        click.echo("Invalid UUID format. Use format: xxxxxxxx-xxxx-xxxx-xxxx-xxxx", err=True)
        sys.exit(1)
    fy_repo = SQLAlchemyFiscalYearRepository()
    service = FiscalYearService(fy_repo)
    try:
        fy = service.create_fiscal_year(
            name=name,
            start_month=start_month,
            start_day=start_day,
            period_type=period_type,
            company_id=company_uuid,
            actor=actor_uuid,
            reason=reason,
        )
        click.echo(
            f"Fiscal year created: {fy.name} ({fy.id}) -- ",
            f"type={fy.period_type.value}, status={fy.status.value}"
        )
    except ValueError as e:
        click.echo(f"Validation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to create fiscal year: {e}", err=True)
        sys.exit(1)



@cli.command("period-create")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--fiscal-year-id", required=True, help="Fiscal year UUID")
@click.option("--name", required=True, help="Period name")
@click.option("--entry-date", required=True, help="Entry date (YYYY-MM-DD)")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", required=True, help="Reason for creation (mandatory per D11)")
@with_appcontext
def period_create(company_id, fiscal_year_id, name, entry_date, actor, reason):
    """Create a new accounting period."""
    from uuid import UUID
    from datetime import datetime
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = None
        if company_id:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                click.echo("Invalid company-id format.", err=True)
        sys.exit(1)
        fy_uuid = None
        if fiscal_year_id:
            try:
                fy_uuid = UUID(fiscal_year_id)
            except ValueError:
                click.echo("Invalid fiscal-year-id format.", err=True)
        sys.exit(1)
        try:
            entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo("Invalid entry-date format. Use YYYY-MM-DD.", err=True)
            sys.exit(1)
        period_repo = SQLAlchemyFiscalYearRepository()
        service = FiscalYearService(fy_repo)
        period = service.create_period(
            company_id=company_uuid,
            fy_id=fy_uuid,
            name=name,
            entry_date=entry_date,
            actor=actor_uuid,
            reason=reason,
        )
        click.echo(
            f"Period created: {period.name} ({period.id}) -- status={period.status.value}"
        )
    except ValueError as e:
        click.echo(f"Cannot create period: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to create period: {e}", err=True)
        sys.exit(1)

@cli.command("period-list")
@click.option("--company-id", help="Filter by company UUID")
@click.option("--fiscal-year-id", help="Filter by fiscal year UUID")
@click.option("--status", type=click.Choice(["OPEN", "LOCKED", "CLOSED"]), help="Filter by period status")
@with_appcontext
def period_list(company_id, fiscal_year_id, status):
    """List accounting periods with optional filters."""
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = None
        if company_id:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                click.echo("Invalid company-id format. Use UUID format (xxxx-xxxx-xxxx-xxxx-xxxx).", err=True)
                sys.exit(1)
        fy_uuid = None
        if fiscal_year_id:
            try:
                fy_uuid = UUID(fiscal_year_id)
            except ValueError:
                click.echo("Invalid fiscal-year-id format.", err=True)
                sys.exit(1)
        period_repo = SQLAlchemyFiscalYearRepository()
        service = FiscalYearService(fy_repo)
        periods = service.list_periods(company_id=company_uuid, fy_id=fy_uuid, status_name=status)
        if not periods:
            click.echo("No periods found matching filters.")
            return
        header = "ID".ljust(36) + "Name".ljust(25) + "FY-ID".ljust(18) + "Status".ljust(10) + "Locked".ljust(8) + "Entry Date"
        click.echo(header)
        click.echo("-" * 96)
        for p in periods:
            entry_str = p.entry_date.strftime("%Y-%m-%d") if p.entry_date else "N/A"
            locked_str = "YES" if p.is_locked else "NO"
            row = p.id.ljust(36) + p.name.ljust(25) + (p.fiscal_year_id.ljust(18) if p.fiscal_year_id else "N/A").ljust(18) + p.status.value.ljust(10) + locked_str.ljust(8) + entry_str
            click.echo(row)
    except Exception as exc:
        click.echo(f"Failed to list periods: {exc}", err=True)
        sys.exit(1)


@cli.command("period-unlock")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--fiscal-year-id", required=True, help="Fiscal year UUID")
@click.option("--period-id", required=True, help="Period UUID")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", required=True, help="Reason for unlocking (mandatory per D11)")
@with_appcontext
def period_unlock(company_id, fiscal_year_id, period_id, actor, reason):
    """Unlock an accounting period."""
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = None
        if company_id:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                click.echo("Invalid company-id format.", err=True)
                sys.exit(1)
        fy_uuid = None
        if fiscal_year_id:
            try:
                fy_uuid = UUID(fiscal_year_id)
            except ValueError:
                click.echo("Invalid fiscal-year-id format.", err=True)
                sys.exit(1)
        period_uuid = None
        if period_id:
            try:
                period_uuid = UUID(period_id)
            except ValueError:
                click.echo("Invalid period-id format.", err=True)
                sys.exit(1)
        period_repo = SQLAlchemyFiscalYearRepository()
        service = FiscalYearService(fy_repo)
        result = service.unlock_period(
            company_id=company_uuid,
            fy_id=fy_uuid,
            period_id=period_uuid,
            actor=actor_uuid,
            reason=reason,
        )
        click.echo(
            f"Period unlocked: {result.name} ({result.id}) -- status={result.status.value}"
        )
    except ValueError as e:
        click.echo(f"Cannot unlock period: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to unlock period: {e}", err=True)
        sys.exit(1)

@cli.command("period-lock")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--fiscal-year-id", required=True, help="Fiscal year UUID")
@click.option("--period-id", required=True, help="Period UUID")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", required=True, help="Reason for locking (mandatory per D11)")
@with_appcontext
def period_lock(company_id, fiscal_year_id, period_id, actor, reason):
    """Lock an accounting period."""
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = None
        if company_id:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                click.echo("Invalid company-id format.", err=True)
                sys.exit(1)
        fy_uuid = None
        if fiscal_year_id:
            try:
                fy_uuid = UUID(fiscal_year_id)
            except ValueError:
                click.echo("Invalid fiscal-year-id format.", err=True)
                sys.exit(1)
        period_uuid = None
        if period_id:
            try:
                period_uuid = UUID(period_id)
            except ValueError:
                click.echo("Invalid period-id format.", err=True)
                sys.exit(1)
        period_repo = SQLAlchemyFiscalYearRepository()
        service = FiscalYearService(fy_repo)
        result = service.lock_period(
            company_id=company_uuid,
            fy_id=fy_uuid,
            period_id=period_uuid,
            actor=actor_uuid,
            reason=reason,
        )
        click.echo(
            f"Period locked: {result.name} ({result.id}) -- status={result.status.value}"
        )
    except ValueError as e:
        click.echo(f"Cannot lock period: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to lock period: {e}", err=True)
        sys.exit(1)

@cli.command("fy-close")
@click.option("--company-id", required=True, help="Company UUID")
@click.option("--actor", required=True, help="Actor UUID (D11 audit requirement)")
@click.option("--reason", required=True, help="Reason for closure (mandatory per D11)")
@with_appcontext
def fy_close(company_id, actor, reason):
    """Close a fiscal year."""
    from uuid import UUID
    from src.application.services.fiscal_year_service import FiscalYearService
    from src.infrastructure.database import db
    from src.infrastructure.repositories.fiscal_year_repo import SQLAlchemyFiscalYearRepository
    try:
        company_uuid = UUID(company_id)
        actor_uuid = UUID(actor)
    except ValueError:
        click.echo("Invalid UUID format. Use format: xxxxxxxx-xxxx-xxxx-xxxx-xxxx", err=True)
        sys.exit(1)
    fy_repo = SQLAlchemyFiscalYearRepository()
    service = FiscalYearService(fy_repo)
    try:
        result = service.close_fiscal_year(
            company_id=company_uuid,
            actor=actor_uuid,
            reason=reason,
        )
        click.echo(
            f"Fiscal year closed: {result.name} ({result.id}) -- ",
            f"status={result.status.value}, opening-balance marker set"
        )
    except ValueError as e:
        click.echo(f"Cannot close fiscal year: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to close fiscal year: {e}", err=True)
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
