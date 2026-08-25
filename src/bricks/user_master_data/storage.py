"""User storage — users table per specs §4.1."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.user_master_data.contract import UserRepositoryPort
from src.bricks.user_master_data.domain import User, UserRole


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(200), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SQLAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(m: UserModel) -> User:
        return User(
            email=m.email,
            role=UserRole(m.role),
            full_name=m.full_name,
            password=m.password,
            id=UUID(m.id),
            is_active=m.is_active,
            last_login=m.last_login,
        )

    def create(self, u: User) -> User:
        self._session.add(
            UserModel(
                id=str(u.id),
                email=u.email,
                password=u.password,
                role=u.role.value,
                full_name=u.full_name,
                is_active=u.is_active,
                last_login=u.last_login,
            )
        )
        self._session.commit()
        return u

    def get_by_id(self, uid: UUID) -> User | None:
        m = self._session.get(UserModel, str(uid))
        return self._to_domain(m) if m else None

    def get_by_email(self, email: str) -> User | None:
        m = self._session.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(m) if m else None

    def update(self, u: User) -> User:
        m = self._session.get(UserModel, str(u.id))
        if m is None:
            raise ValueError("not found")
        m.password = u.password
        m.role = u.role.value
        m.full_name = u.full_name
        m.is_active = u.is_active
        m.last_login = u.last_login
        self._session.commit()
        return u

    def email_exists(self, email: str) -> bool:
        row = self._session.query(UserModel.id).filter(UserModel.email == email).first()
        return row is not None
