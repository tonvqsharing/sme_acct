"""User/auth web adapter — login, logout, me, user CRUD."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from src.bricks.user_master_data.domain import InvalidEmailError, UserRole
from src.bricks.user_master_data.services import (
    ActorRequiredError,
    DuplicateEmailError,
    InactiveAccountError,
    InvalidCredentialsError,
    NotFoundError,
)

auth_bp = Blueprint("auth", __name__)
users_bp = Blueprint("users", __name__)

_user_service: Any = None


def init_user_service(svc: Any) -> None:
    global _user_service
    _user_service = svc


def _svc() -> Any:
    s = _user_service
    if s is None:
        abort(500, description="UserService not initialized")
    return s


def ser_user(u: Any) -> dict[str, Any]:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role.value if hasattr(u.role, "value") else str(u.role),
        "is_active": bool(getattr(u, "is_active", True)),
    }


# ─── Auth ──────────────────────────────────────────────────────────────────


@auth_bp.post("/api/v1/auth/login")
def login() -> tuple[Any, int]:
    """Session-based login. Sets Flask-Login cookie."""
    body = request.get_json(silent=True) or {}
    email = body.get("email", "")
    password = body.get("password", "")
    try:
        user = _svc().authenticate(email, password)
    except (InvalidCredentialsError, InactiveAccountError):
        return (
            jsonify(
                {
                    "error": "Email hoặc mật khẩu không đúng",
                    "code": "INVALID_CREDENTIALS",
                }
            ),
            401,
        )
    login_user(user)
    return jsonify({"data": ser_user(user)}), 200


@auth_bp.post("/api/v1/auth/logout")
@login_required  # type: ignore[untyped-decorator]
def logout() -> tuple[Any, int]:
    logout_user()
    return jsonify({"data": {"status": "logged_out"}}), 200


@auth_bp.get("/api/v1/auth/me")
@login_required  # type: ignore[untyped-decorator]
def me() -> tuple[Any, int]:
    return (
        jsonify(
            {
                "data": {
                    "id": str(current_user.id),
                    "email": getattr(current_user, "email", ""),
                    "role": (
                        current_user.role.value
                        if hasattr(current_user.role, "value")
                        else str(current_user.role)
                    ),
                }
            }
        ),
        200,
    )


# ─── User CRUD (ADMIN only per specs §5.1) ────────────────────────────────


def _admin_only() -> None:
    role = getattr(current_user, "role", "")
    value = role.value if hasattr(role, "value") else str(role)
    if value != "ADMIN":
        abort(403)


@users_bp.post("/api/v1/users")
def create_user() -> tuple[Any, int]:
    _admin_only()
    body = request.get_json(silent=True) or {}
    u: Any = None
    try:
        u = _svc().create_user(
            email=body["email"],
            password=body["password"],
            role=UserRole(body.get("role", "accountant")),
            full_name=body.get("full_name", ""),
            actor=UUID(str(current_user.id)),
        )
    except DuplicateEmailError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_EMAIL"}), 409
    except InvalidEmailError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_EMAIL"}), 422
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "WEAK_PASSWORD"}), 422
    except ActorRequiredError as exc:
        return jsonify({"error": str(exc), "code": "MISSING_ACTOR"}), 400
    except KeyError as exc:
        abort(422, description=f"missing {exc}")
    return jsonify({"data": ser_user(u)}), 201


@users_bp.get("/api/v1/users/<uid>")
@login_required  # type: ignore[untyped-decorator]
def get_user(uid: str) -> tuple[Any, int]:
    _admin_only()
    try:
        u = _svc().get_by_id(UUID(uid))
    except ValueError:
        abort(422, description="Invalid UUID")
    if u is None:
        abort(404)
    return jsonify({"data": ser_user(u)}), 200


@users_bp.post("/api/v1/users/<uid>/reset-password")
def reset_password(uid: str) -> tuple[Any, int]:
    _admin_only()
    body = request.get_json(silent=True) or {}
    u: Any = None
    try:
        u = _svc().reset_password(
            UUID(uid),
            body["password"],
            actor=UUID(str(current_user.id)),
        )
    except KeyError as exc:
        abort(422, description=f"missing {exc}")
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "WEAK_PASSWORD"}), 422
    except NotFoundError:
        abort(404)
    return jsonify({"data": {"id": str(u.id), "reset": True}}), 200


@users_bp.post("/api/v1/users/<uid>/deactivate")
def deactivate_user(uid: str) -> tuple[Any, int]:
    _admin_only()
    try:
        u = _svc().deactivate(UUID(uid), actor=UUID(str(current_user.id)))
    except NotFoundError:
        abort(404)
    return jsonify({"data": ser_user(u)}), 200
