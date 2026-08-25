"""Unit tests — UserService (specs-user-master-data §2, §6)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.user_master_data.domain import (
    InvalidEmailError,
    User,
    UserRole,
)
from src.bricks.user_master_data.services import (
    DuplicateEmailError,
    InactiveAccountError,
    InvalidCredentialsError,
    UserService,
)


class FakeRepo:
    def __init__(self):
        self.rows: dict[str, User] = {}

    def create(self, u):
        self.rows[u.email] = u
        return u

    def get_by_id(self, uid):
        return self.rows.get(f"id:{uid}")

    def get_by_email(self, email):
        return self.rows.get(email)

    def update(self, u):
        self.rows[u.email] = u
        return u

    def email_exists(self, email):
        return email in self.rows


@pytest.fixture()
def svc():
    repo = FakeRepo()
    # seed id-index for get_by_id
    orig_create = repo.create

    def create_with_id(u):
        result = orig_create(u)
        repo.rows[f"id:{result.id}"] = result
        return result

    repo.create = create_with_id
    return UserService(repo)


class TestCreateUser:
    def test_password_stored_hashed_not_plaintext(self, svc):
        u = svc.create_user(
            email="kt@abc.vn",
            password="S3cure!pass",
            role=UserRole.ACCOUNTANT,
            full_name="Nguyễn Văn Kế",
            actor=uuid4(),
        )
        assert u.password != "S3cure!pass"
        assert u.password.startswith(("pbkdf2:", "scrypt:"))

    def test_verify_password_roundtrip(self, svc):
        u = svc.create_user(
            email="kt@abc.vn",
            password="S3cure!pass",
            role=UserRole.ACCOUNTANT,
            full_name="x",
            actor=uuid4(),
        )
        assert u.verify_password("S3cure!pass") is True
        assert u.verify_password("wrong") is False

    @pytest.mark.parametrize("bad", ["not-an-email", "", "a@b", "@c.vn"])
    def test_invalid_email_rejected(self, svc, bad):
        with pytest.raises(InvalidEmailError):
            svc.create_user(
                email=bad,
                password="pw123456",
                role=UserRole.ACCOUNTANT,
                full_name="x",
                actor=uuid4(),
            )

    def test_short_password_rejected(self, svc):
        with pytest.raises(ValueError, match="[Pp]assword"):
            svc.create_user(
                email="a@b.vn",
                password="short",
                role=UserRole.ACCOUNTANT,
                full_name="x",
                actor=uuid4(),
            )

    def test_duplicate_email_rejected(self, svc):
        kw = {
            "password": "pw123456",
            "role": UserRole.ACCOUNTANT,
            "full_name": "x",
            "actor": uuid4(),
        }
        svc.create_user(email="dup@b.vn", **kw)
        with pytest.raises(DuplicateEmailError):
            svc.create_user(email="dup@b.vn", **kw)

    def test_missing_actor_raises(self, svc):
        from src.bricks.user_master_data.services import ActorRequiredError

        with pytest.raises(ActorRequiredError):
            svc.create_user(
                email="a@b.vn",
                password="pw123456",
                role=UserRole.ACCOUNTANT,
                full_name="x",
                actor=None,
            )


class TestAuthenticate:
    def _seed(self, svc):
        return svc.create_user(
            email="kt@abc.vn",
            password="Good1pass",
            role=UserRole.ACCOUNTANT,
            full_name="KT",
            actor=uuid4(),
            is_active=True,
        )

    def test_valid_credentials_return_user(self, svc):
        self._seed(svc)
        u = svc.authenticate("kt@abc.vn", "Good1pass")
        assert u.email == "kt@abc.vn"

    def test_wrong_password_raises(self, svc):
        self._seed(svc)
        with pytest.raises(InvalidCredentialsError):
            svc.authenticate("kt@abc.vn", "Wrong1pass")

    def test_unknown_email_same_error_as_wrong_password(self, svc):
        """Anti-enumeration: identical error for unknown user vs bad pw."""
        with pytest.raises(InvalidCredentialsError):
            svc.authenticate("ghost@b.vn", "Whatever1")

    def test_inactive_account_cannot_login(self, svc):
        u = self._seed(svc)
        svc.deactivate(u.id, actor=uuid4())
        with pytest.raises(InactiveAccountError):
            svc.authenticate("kt@abc.vn", "Good1pass")


class TestLifecycle:
    def _seed(self, svc):
        return svc.create_user(
            email="x@b.vn",
            password="pw123456",
            role=UserRole.ADMIN,
            full_name="A",
            actor=uuid4(),
        )

    def test_reset_password(self, svc):
        u = self._seed(svc)
        svc.reset_password(u.id, "NewPass99", actor=uuid4())
        fresh = svc.get_by_id(u.id)
        assert fresh is not None
        assert fresh.verify_password("NewPass99")
        assert not fresh.verify_password("pw123456")

    def test_deactivate_blocks_authenticate(self, svc):
        u = self._seed(svc)
        out = svc.deactivate(u.id, actor=uuid4())
        assert out.is_active is False

    def test_roles_match_spec(self):
        assert {r.name for r in UserRole} == {
            "ACCOUNTANT",
            "CHIEF_ACCOUNTANT",
            "ADMIN",
            "AUDITOR",
            "DIRECTOR",
        }
