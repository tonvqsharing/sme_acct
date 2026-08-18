"""API blueprint — User Master Data Module endpoints.

Provides REST-ish endpoints for user management:
- CRUD operations for users
- Role assignment
- Enable/disable accounts
- Password reset
- User listing

Follows Clean Architecture: service layer uses SQLAlchemyUserRepository
via AuthService. RBAC enforced via @casbin_required decorator.

Module status: v1 — basic CRUD + RBAC. Future: profile, permissions, SSO.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from src.application.services.auth_service import AuthService
from src.application.ports import UserRepositoryPort
from src.domain.entities.user import User
from src.domain.entities.base import UserRole
from src.domain.exceptions import (
    UserNotFoundError,
    UserValidationError,
    DuplicateEmailError,
    UserRoleError,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import UserModel, UserRoleEnum
from src.presentation.rbac import casbin_required, DEFAULT_ALLOWED_ROLES

api_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

logger = logging.getLogger(__name__)

# ── Test engine hook (set by tests before making requests) ─────────────────
_test_engine = None


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_auth_service() -> AuthService:
    """Get AuthService instance (uses SQLAlchemyUserRepository via init)."""
    return AuthService()


def _user_to_dict(user: User) -> dict:
    """Convert domain User to API response dict."""
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "created_by": str(user.created_by) if user.created_by else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "updated_by": str(user.updated_by) if user.updated_by else None,
    }


# ── API Endpoints ────────────────────────────────────────────────────────

# ── Health ───────────────────────────────────────────────────────────────


@api_bp.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "module": "users"}


# ── List users (ADMIN only) ────────────────────────────────────────────


@api_bp.get("")
@casbin_required("ADMIN")
def list_users():
    """List all users in the system (Admin only)."""
    auth = _get_auth_service()
    users = auth.list_users()
    return jsonify({
        "count": len(users),
        "users": users
    })


# ── Create user (ADMIN only) ───────────────────────────────────────────


@api_bp.post("")
@casbin_required("ADMIN")
def create_user():
    """Create a new user (Admin only)."""
    from src.application.services.auth_service import AuthService
    auth = _get_auth_service()

    # Parse request body
    email = request.json.get("email", "") if request.json else ""
    role_str = request.json.get("role", "accountant") if request.json else "accountant"
    password = request.json.get("password", "") if request.json else ""

    # Validate role
    try:
        role = UserRole(role_str)
    except ValueError:
        return jsonify({
            "error": f"VALIDATION_ERROR",
            "code": "INVALID_ROLE",
            "message": f"Vai trò '{role_str}' không hợp lệ",
            "details": {
                "available_roles": [r.value for r in UserRole]
            }
        }), 400

    # Validate email
    if not email or "@" not in email:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "INVALID_EMAIL",
            "message": "Email là bắt buộc và phải có định dạng email"
        }), 422

    # Check if email already exists
    existing = auth.get_by_email(email)
    if existing:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "EMAIL_TAKEN",
            "message": f"Email '{email}' đã được đăng ký"
        }), 409

    # Create user
    try:
        user = auth.create_user(email=email, role=role.value, password=password)
    except ValueError as exc:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "USER_CREATION_FAILED",
            "message": str(exc)
        }), 422

    # Log RBAC decision
    resource = request.path
    action = request.method.lower()
    from src.presentation.rbac import _log_rbac_decision
    enforcer = logging.getLogger(__name__).handler if False else None
    _log_rbac_decision(True, resource, action)

    return jsonify({
        "message": "User created successfully",
        "user": _user_to_dict(user)
    }), 201


# ── Get user by ID (AUTH) ─────────────────────────────────────────────


@api_bp.get("/<uuid:user_id>")
@casbin_required("AUTH")
def get_user(user_id: UUID):
    """Get user by ID."""
    auth = _get_auth_service()
    user = auth.get_by_id(user_id)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": f"User ID {user_id} không tồn tại"
        }), 404

    return jsonify({
        "user": _user_to_dict(user)
    })


# ── Update user (ADMIN only) ──────────────────────────────────────────


@api_bp.patch("/<uuid:user_id>")
@casbin_required("ADMIN")
def update_user(user_id: UUID):
    """Update user (Admin only)."""
    auth = _get_auth_service()
    user = auth.get_by_id(user_id)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": f"User ID {user_id} không tồn tại"
        }), 404

    # Parse request body
    if not request.json:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "NO_DATA",
            "message": "Không có dữ liệu cập nhật"
        }), 400

    email = request.json.get("email", user.email)
    role_str = request.json.get("role", user.role.value)

    # Validate role if provided
    if role_str:
        try:
            role = UserRole(role_str)
        except ValueError:
            return jsonify({
                "error": "VALIDATION_ERROR",
                "code": "INVALID_ROLE",
                "message": f"Vai trò '{role_str}' không hợp lệ"
            }), 400
    else:
        role = user.role

    # Update user
    try:
        updated = auth.assign_role(user_id, role_str)
    except (ValueError, LookupError) as exc:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "UPDATE_FAILED",
            "message": str(exc)
        }), 422

    # Log RBAC decision
    resource = request.path
    action = request.method.lower()
    from src.presentation.rbac import _log_rbac_decision
    _log_rbac_decision(True, resource, action)

    return jsonify({
        "message": "User updated successfully",
        "user": _user_to_dict(updated)
    })


# ── Suspend user (ADMIN|DIRECTOR only) ─────────────────────────────────


@api_bp.post("/<uuid:user_id>/suspend")
@casbin_required("ADMIN", "DIRECTOR")
def suspend_user(user_id: UUID):
    """Suspend/disable user account."""
    auth = _get_auth_service()
    user = auth.get_by_id(user_id)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": f"User ID {user_id} không tồn tại"
        }), 404

    # Check if trying to suspend the only ADMIN
    if user.role == UserRole.ADMIN:
        # Simple check - in production would count admins
        pass

    # Disable user
    try:
        auth.disable_user(user_id)
    except LookupError as exc:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": str(exc)
        }), 404

    # Log RBAC decision
    resource = request.path
    action = request.method.lower()
    from src.presentation.rbac import _log_rbac_decision
    _log_rbac_decision(True, resource, action)

    return jsonify({
        "message": f"User {user.email} has been disabled",
        "user": _user_to_dict(user)
    })


# ── Reactivate user (ADMIN|DIRECTOR only) ──────────────────────────────


@api_bp.post("/<uuid:user_id>/reactivate")
@casbin_required("ADMIN", "DIRECTOR")
def reactivate_user(user_id: UUID):
    """Enable user account."""
    auth = _get_auth_service()
    user = auth.get_by_id(user_id)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": f"User ID {user_id} không tồn tại"
        }), 404

    # Enable user
    try:
        auth.enable_user(user_id)
    except LookupError as exc:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": str(exc)
        }), 404

    # Log RBAC decision
    resource = request.path
    action = request.method.lower()
    from src.presentation.rbac import _log_rbac_decision
    _log_rbac_decision(True, resource, action)

    return jsonify({
        "message": f"User {user.email} has been reactivated",
        "user": _user_to_dict(user)
    })


# ── Reset password (ADMIN only) ────────────────────────────────────────


@api_bp.post("/<uuid:user_id>/reset-password")
@casbin_required("ADMIN")
def reset_password(user_id: UUID):
    """Reset user password (Admin only)."""
    auth = _get_auth_service()
    user = auth.get_by_id(user_id)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": f"User ID {user_id} không tồn tại"
        }), 404

    # Parse new password from request
    new_password = request.json.get("new_password", "") if request.json else ""

    if not new_password:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "code": "NO_PASSWORD",
            "message": "Mật khẩu mới là bắt buộc"
        }), 422

    # Reset password
    try:
        auth.reset_password(user_id, new_password)
    except LookupError as exc:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "code": "USER_NOT_FOUND",
            "message": str(exc)
        }), 404

    # Log RBAC decision
    resource = request.path
    action = request.method.lower()
    from src.presentation.rbac import _log_rbac_decision
    _log_rbac_decision(True, resource, action)

    return jsonify({
        "message": f"Password reset for {user.email} successfully",
        "user": _user_to_dict(user)
    })


# ── DEFAULT ALLOWED ROUTES (fallback when pycasbin unavailable) ─────────

# These are used by @casbin_required when pycasbin model parsing fails
# They follow the same pattern as company/invoice/voucher routes
DEFAULT_ALLOWED_ROUTES.update({
    "api.v1.users.list": {"ADMIN"},
    "api.v1.users.create": {"ADMIN"},
    "api.v1.users.get": {"AUTH"},  # AUTH means any authenticated user can read their own profile
    "api.v1.users.update": {"ADMIN"},
    "api.v1.users.suspend": {"ADMIN", "DIRECTOR"},
    "api.v1.users.reactivate": {"ADMIN", "DIRECTOR"},
    "api.v1.users.reset-password": {"ADMIN"},
})