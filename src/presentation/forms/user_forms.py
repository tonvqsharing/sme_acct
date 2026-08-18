"""WTForms for User Master Data module."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class UserCreateForm(FlaskForm):
    """Form for creating new users (Admin only)."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email là bắt buộc"),
            Email(message="Định dạng email không hợp lệ"),
            Length(max=120, message="Email tối đa 120 ký tự"),
        ],
        render_kw={"placeholder": "user@don-vi.vn"},
    )

    role = SelectField(
        "Vai trò",
        choices=[
            ("accountant", "Kế toán viên (ACCOUNTANT)"),
            ("chief_accountant", "Kế toán trưởng (CHIEF_ACCOUNTANT)"),
            ("admin", "Admin (ADMIN)"),
            ("auditor", "Kiểm toán viên (AUDITOR)"),
            ("director", "Giám đốc (DIRECTOR)"),
        ],
        validators=[DataRequired(message="Vai trò là bắt buộc")],
        render_kw={"class": "form-select"},
    )

    password = PasswordField(
        "Mật khẩu",
        validators=[
            DataRequired(message="Mật khẩu là bắt buộc"),
            Length(min=8, message="Mật khẩu ít nhất 8 ký tự"),
        ],
        render_kw={"placeholder": "TempPass123!", "class": "form-control"},
    )

    is_active = BooleanField("Kích hoạt ngay lập tức", default=True)

    submit = SubmitField("Tạo user", render_kw={"class": "btn btn-primary"})


class UserUpdateForm(FlaskForm):
    """Form for updating user (role, active status). Admin only."""

    role = SelectField(
        "Vai trò",
        choices=[
            ("accountant", "Kế toán viên"),
            ("chief_accountant", "Kế toán trưởng"),
            ("admin", "Admin"),
            ("auditor", "Kiểm toán viên"),
            ("director", "Giám đốc"),
        ],
        validators=[DataRequired(message="Vai trò là bắt buộc")],
        render_kw={"class": "form-select"},
    )

    is_active = BooleanField("Kích hoạt tài khoản")

    submit = SubmitField("Cập nhật", render_kw={"class": "btn btn-primary"})


class PasswordResetForm(FlaskForm):
    """Form for resetting user password (Admin only)."""

    new_password = PasswordField(
        "Mật khẩu mới",
        validators=[
            DataRequired(message="Mật khẩu mới là bắt buộc"),
            Length(min=8, message="Ít nhất 8 ký tự"),
        ],
        render_kw={"placeholder": "NewPass123!", "class": "form-control"},
    )

    confirm_password = PasswordField(
        "Xác nhận mật khẩu",
        validators=[
            DataRequired(message="Xác nhận mật khẩu là bắt buộc"),
            EqualTo("new_password", message="Mật khẩu không khớp"),
        ],
        render_kw={"placeholder": "NewPass123!", "class": "form-control"},
    )

    submit = SubmitField("Đặt lại mật khẩu", render_kw={"class": "btn btn-primary"})


class UserSearchForm(FlaskForm):
    """Form for searching users by email or role."""
    email = StringField("Email tìm kiếm")

    role = SelectField(
        "Vai trò",
        choices=[
            ("", "Tất cả"),
            ("accountant", "Kế toán viên"),
            ("chief_accountant", "Kế toán trưởng"),
            ("admin", "Admin"),
            ("auditor", "Kiểm toán viên"),
            ("director", "Giám đốc"),
        ],
        render_kw={"class": "form-select"},
    )

    submit = SubmitField("Tìm kiếm", render_kw={"class": "btn btn-primary"})