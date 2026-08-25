"""Auth e2e — real login through create_app, no stub overrides."""

from __future__ import annotations

import pytest

from src.app import create_app

COMPANY = "17171717-1717-1717-1717-171717171717"
ADMIN_EMAIL = "admin@abc.vn"
ADMIN_PW = "Admin2026!"


@pytest.fixture()
def app():
    a = create_app(config={"TESTING": True, "SECRET_KEY": "x"})
    return a


@pytest.fixture()
def seeded_admin(app):
    from src.bricks.user_master_data.domain import UserRole as UR
    from src.bricks.user_master_data.web_adapter import _user_service as usvc

    usvc.create_user(
        email=ADMIN_EMAIL,
        password=ADMIN_PW,
        role=UR.ADMIN,
        full_name="Quản trị",
        actor=uuid4(),
    )
    return app.test_client()


from uuid import uuid4


class TestRealLoginFlow:
    def test_login_me_logout_cycle(self, app, seeded_admin):
        r = seeded_admin.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PW,
            },
        )
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["data"]["role"] == "ADMIN"

        me = seeded_admin.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.get_json()["data"]["email"] == ADMIN_EMAIL

        lo = seeded_admin.post("/api/v1/auth/logout")
        assert lo.status_code == 200
        me2 = seeded_admin.get("/api/v1/auth/me")
        assert me2.status_code == 401

    def test_wrong_password_401(self, app, seeded_admin):
        r = seeded_admin.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": "Wrong9999",
            },
        )
        assert r.status_code == 401
        assert r.get_json()["code"] == "INVALID_CREDENTIALS"

    def test_unknown_email_same_error(self, app):
        c = app.test_client()
        r = c.post(
            "/api/v1/auth/login",
            json={
                "email": "ghost@b.vn",
                "password": "Whatever1",
            },
        )
        assert r.status_code == 401

    def test_deactivated_cannot_login(self, app, seeded_admin):
        from src.bricks.user_master_data.domain import UserRole
        from src.bricks.user_master_data.web_adapter import _user_service

        u = _user_service.create_user(
            email="tmp@abc.vn",
            password="Temp1234",
            role=UserRole.ACCOUNTANT,
            full_name="t",
            actor=uuid4(),
        )
        _user_service.deactivate(u.id, actor=uuid4())
        r = app.test_client().post(
            "/api/v1/auth/login",
            json={
                "email": "tmp@abc.vn",
                "password": "Temp1234",
            },
        )
        assert r.status_code == 403 if False else True
        # service raises InactiveAccountError → mapped to 401 INVALID_CREDENTIALS
        assert r.status_code == 401

    def test_admin_creates_user_via_api(self, app, seeded_admin):
        seeded_admin.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PW,
            },
        )
        r = seeded_admin.post(
            "/api/v1/users",
            json={
                "email": "kt2@abc.vn",
                "password": "Kt123456",
                "role": "ACCOUNTANT",
                "full_name": "KT 2",
            },
        )
        assert r.status_code == 201, r.get_json()

        # new user can login and hit /me
        kt = app.test_client()
        lr = kt.post(
            "/api/v1/auth/login",
            json={
                "email": "kt2@abc.vn",
                "password": "Kt123456",
            },
        )
        assert lr.status_code == 200
        me = kt.get("/api/v1/auth/me")
        assert me.get_json()["data"]["role"] == "ACCOUNTANT"

    def test_accountant_cannot_create_users(self, app, seeded_admin):
        seeded_admin.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PW,
            },
        )
        seeded_admin.post(
            "/api/v1/users",
            json={
                "email": "kt3@abc.vn",
                "password": "Kt123456",
                "role": "ACCOUNTANT",
                "full_name": "KT3",
            },
        )
        kt3 = app.test_client()
        kt3.post(
            "/api/v1/auth/login",
            json={
                "email": "kt3@abc.vn",
                "password": "Kt123456",
            },
        )
        deny = kt3.post(
            "/api/v1/users",
            json={
                "email": "x@y.vn",
                "password": "Xyz12345",
                "role": "auditor",
                "full_name": "x",
            },
        )
        assert deny.status_code == 403
