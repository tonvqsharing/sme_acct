# Templates: User Master Data Module

## 1. WTForms (Flask-WTF forms)

### 1.1 UserCreateForm (`src/presentation/forms/user_forms.py` — new)

```python
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField
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
```

### 1.2 UserUpdateForm (`src/presentation/forms/user_forms.py` — extend)

```python
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
```

### 1.3 PasswordResetForm (`src/presentation/forms/user_forms.py` — new)

```python
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
```

---

## 2. HTML Templates

### 2.1 user_list.html (`src/presentation/templates/user/user_list.html`)

```html
{% extends "base.html" %}
{% block title %}Danh sách user - Hệ thống kế toán SME{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Danh sách người dùng hệ thống</h2>
    
    <table class="table table-striped table-bordered">
        <thead>
            <tr>
                <th>Email</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Last login</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
        {% for user in users %}
            <tr>
                <td>{{ user.email }}</td>
                <td>
                    <span class="badge bg-{{ user.role == 'admin' | success_class }}">
                        {{ user.role | title }}
                    </span>
                </td>
                <td>
                    <span class="badge bg-{{ user.is_active | success_inverse_class }}">
                        {% if user.is_active %}ACTIVE{% else %}DISABLED{% endif %}
                    </span>
                </td>
                <td>{{ user.last_login or 'Chưa ever login' }}</td>
                <td>
                    <a href="/users/{{ user.id }}/detail" class="btn btn-sm btn-outline-primary">Chi tiết</a>
                    <a href="/users/{{ user.id }}/edit" class="btn btn-sm btn-outline-warning">Sửa</a>
                    <form action="/users/{{ user.id }}/delete" method="POST" style="display:inline;">
                        <button class="btn btn-sm btn-outline-danger" onclick="return confirm('Xóa vĩnh viern này?');">Xóa</button>
                    </form>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="5" class="text-center">Không có user nào trong hệ thống.</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    
    <a href="/users/create" class="btn btn-success">Tạo user mới</a>
    <a href="/dashboard" class="btn btn-secondary">Quay về dashboard</a>
</div>
{% endblock %}
```

---

### 2.2 user_form.html (shared create/edit template)

```html
{% extends "base.html" %}
{% block title %}
{% if form.instance and form.instance.id %}Sửa user{% else %}Tạo user mới{% endif %}
{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>{% if form.instance and form.instance.id %}Sửa user{% else %}Tạo user mới{% endif %}</h2>
    
    <form method="POST" novalidate>
        {{ form.hidden_tag() }}
        
        <div class="mb-3">
            <label for="email">Email <span class="text-danger">*</span></label>
            {{ form.email(class="form-control", placeholder="user@don-vi.vn") }}
            {% if form.errors.get('email') %}
                <div class="text-danger small">{{ form.errors['email'][0] }}</div>
            {% endif %}
        </div>
        
        <div class="mb-3">
            <label for="role">Vai trò <span class="text-danger">*</span></label>
            {{ form.role(class="form-select") }}
            {% if form.errors.get('role') %}
                <div class="text-danger small">{{ form.errors['role'][0] }}</div>
            {% endif %}
        </div>
        
        {% if is_reset %}
            <div class="mb-3">
                <label for="new_password">Mật khẩu mới <span class="text-danger">*</span></label>
                {{ form.new_password(class="form-control", placeholder="NewPass123!") }}
                {% if form.errors.get('new_password') %}
                    <div class="text-danger small">{{ form.errors['new_password'][0] }}</div>
                {% endif %}
            </div>
            
            <div class="mb-3">
                <label for="confirm_password">Xác nhận mật khẩu <span class="text-danger">*</span></label>
                {{ form.confirm_password(class="form-control", placeholder="NewPass123!") }}
                {% if form.errors.get('confirm_password') %}
                    <div class="text-danger small">{{ form.errors['confirm_password'][0] }}</div>
                {% endif %}
            </div>
        {% endif %}
        
        <div class="mb-3 form-check">
            {{ form.is_active(class="form-check-input") }}
            <label class="form-check-label" for="is_active">
                Kích hoạt tài khoản
            </label>
        </div>
        
        {{ form.submit(class="btn btn-primary") }}
        <a href="/users" class="btn btn-link">Huỷ bỏ</a>
    </form>
</div>
{% endblock %}
```

---

### 2.3 user_detail.html

```html
{% extends "base.html" %}
{% block title %Chi tiết user: {{ user.email }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Chi tiết user: {{ user.email }}</h2>
    
    <div class="row">
        <div class="col-md-4">
            <p><strong>Email:</strong> {{ user.email }}</p>
            <p><strong>Vai trò:</strong> 
                <span class="badge bg-primary">
                    {{ user.get_role_display() | default(user.role | title) }}
                </span>
            </p>
            <p><strong>Trạng thái:</strong> 
                <span class="badge bg-{{ user.is_active | success_inverse_class }}">
                    {% if user.is_active %}ACTIVE{% else %}DISABLED{% endif %}
                </span>
            </p>
            <p><strong>Created at:</strong> {{ user.created_at }}</p>
            <p><strong>Created by:</strong> {{ user.created_by_name | user_name }}</p>
            <p><strong>Last login:</strong> {{ user.last_login or 'Chưa ever login' }}</p>
            <p><strong>Config version:</strong> {{ user.config_version }}</p>
        </div>
        
        <div class="col-md-4">
            <p><strong>Updated at:</strong> {{ user.updated_at | default('Chưa bao giờ update') }}</p>
            <p><strong>Updated by:</strong> {{ user.updated_by_name | user_name | default('Chưa bao giờ') }}</p>
            <hr>
            <h5>Hoạt động gần đây:</h5>
            <ul class="list-unstyled">
                {% for action in user.recent_actions %}
                    <li>
                        <strong>{{ action.action | upper }}</strong> 
                        vào lúc {{ action.changed_at | default(action.created_at) }}
                        {% if action.actor_id %}bởi user {{ action.actor_id }}{% endif %}
                        {% if action.before_value %}(từ: {{ action.before_value }}){% endif %}
                        {% if action.after_value %}(thành: {{ action.after_value }}){% endif %}
                    </li>
                {% empty %}
                    <li class="text-muted">Chưa có hoạt động logged.</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="col-md-4">
            <hr>
            <h5>Hành động có thể thực hiện:</h5>
            <ul class="list-unstyled">
                {% if current_user.is_admin or current_user.is_director %}
                    <li><a href="/users/{{ user.id }}/edit">Sửa user</a></li>
                    <li><a href="/users/{{ user.id }}/reset-password">Đặt lại mật khẩu</a></li>
                    {% if user.id != current_user.id %}
                        <li><a href="/users/{{ user.id }}/suspend">Vô hiệu hóa tài khoản</a></li>
                        {% if not user.is_active %}
                            <li><a href="/users/{{ user.id }}/reactivate">Kích hoạt lại</a></li>
                        {% endif %}
                    {% endif %}
                {% endif %}
                {% if current_user.is_director %}
                    <li><a href="/users/{{ user.id }}/delete">Xóa vĩnh viễn</a></li>
                {% endif %}
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

---

### 2.4 base.html (already exists — verify it includes user context)

The existing `templates/base.html` already uses Bulma + HTMX (offline-capable). No changes needed unless adding user-specific toolbar.

---

## 3. API Response Templates (JSON)

### 3.1 User Response (GET /api/v1/users/{id})

```json
{
    "id": "uuid-string",
    "email": "accountant@sme-acct.local",
    "role": "accountant",
    "is_active": true,
    "last_login": "2026-08-17T10:30:00Z",
    "created_at": "2026-08-17T08:15:00Z",
    "created_by": "uuid-string",
    "updated_at": "2026-08-17T10:30:00Z",
    "updated_by": "uuid-string"
}
```

### 3.2 User List Response (GET /api/v1/users)

```json
{
    "count": 5,
    "users": [
        {
            "id": "uuid-1",
            "email": "admin@sme-acct.local",
            "role": "admin",
            "is_active": true,
            "last_login": "2026-08-17T14:20:00Z"
        },
        {
            "id": "uuid-2",
            "email": "ca@sme-acct.local",
            "role": "chief_accountant",
            "is_active": true,
            "last_login": "2026-08-17T09:15:00Z"
        }
        // ... more users
    ]
}
```

### 3.3 Error Response (422 Validation)

```json
{
    "error": "VALIDATION_ERROR",
    "code": "INVALID_EMAIL",
    "message": "Email này đã được đăng ký",
    "details": {
        "email": ["Email đã tồn tại trong hệ thống."]
    }
}
```

### 3.4 RBAC Denied Response (403)

```json
{
    "error": "RBAC denied",
    "code": "RBAC_DENIED",
    "message": "RBAC denied: role 'accountant' cannot 'POST' '/api/v1/invoices'",
    "details": {
        "required_role": "ACCOUNTANT or CHIEF_ACCOUNTANT",
        "user_role": "accountant",
        "resource": "/api/v1/invoices",
        "action": "POST"
    }
}
```

---

## 4. CLI Script Templates (manage.py commands)

### 4.1 create-admin (already exists — verify)

Already in `scripts/manage.py` — no changes needed for v1.

### 4.2 create-user (already exists — verify)

Already in `scripts/manage.py` — no changes needed for v1 (raw SQL under the hood).

### 4.3 New CLI templates for future use:

```
# create-user-enhanced (future: SQLAlchemy-based)
uv run python -c "
from src.application.services.auth_service import AuthService
auth = AuthService()
user = auth.create_user('acct@sme-acct.local', 'accountant', 'TempPass123!')
print(f'User: {user.email_val} (id={user.id}) — role={user.role_val}')
"
```

```
# list-users-enhanced (future)
uv run python -c "
from src.application.services.auth_service import AuthService
auth = AuthService()
users = auth.list_users()
for u in users:
    status = 'ACTIVE' if u['is_active'] else 'DISABLED'
    print(f'{u[\"email\"]:30s}  role={u[\"role\"]:15s}  status={status:8s}')
"
```