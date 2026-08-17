"""Database engine and session setup — stub."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass


def init_db(app: Flask) -> None:
    db.init_app(app)
    with app.app_context():
        db.create_all()
