"""Storage — no DB for conversion (stateless). Provides Base for alembic."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
