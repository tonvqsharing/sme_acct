"""Shared integration fixtures: real create_app + Flask-Login stubs."""

from __future__ import annotations

import pytest
from flask_login import UserMixin

from src.app import create_app

_store: dict = {}

UUID_ADMIN = "00000000-0000-0000-0000-000000000001"
UUID_ACCOUNTANT = "00000000-0000-0000-0000-000000000002"
UUID_CHIEF = "00000000-0000-0000-0000-000000000003"
UUID_AUDITOR = "00000000-0000-0000-0000-000000000004"


class FakeUser(UserMixin):
    def __init__(self, user_id: str, role: str):
        self.id = user_id
        self.role = role


@pytest.fixture(autouse=True)
def _clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture()
def app():
    application = create_app(config={"TESTING": True, "SECRET_KEY": "test-secret"})
    login_manager = application.login_manager

    @login_manager.user_loader
    def load_user(user_id: str):
        return _store.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        return "", 401

    return application


def _client(app, user_id: str, role: str):
    user = FakeUser(user_id, role)
    _store[user.id] = user
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = user.id
    return c


@pytest.fixture()
def admin_client(app):
    return _client(app, UUID_ADMIN, "ADMIN")


@pytest.fixture()
def accountant_client(app):
    return _client(app, UUID_ACCOUNTANT, "ACCOUNTANT")


@pytest.fixture()
def chief_client(app):
    return _client(app, UUID_CHIEF, "CHIEF_ACCOUNTANT")


@pytest.fixture()
def auditor_client(app):
    return _client(app, UUID_AUDITOR, "AUDITOR")
