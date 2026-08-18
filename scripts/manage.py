"""CLI management commands for Vietnamese SME Accounting Application.

Provides user/role management commands:
- create-admin: Create first admin user
- reset-password: Reset user password
- assign-role: Assign role to user
- enable-user: Enable user account
- disable-user: Disable user account
- list-users: List all users with roles

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
            f"User created: {user.email_val} (id={user.id}) — "
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
            f"Admin created: {admin.email} ({admin.id}) — "
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


if __name__ == "__main__":
    cli()