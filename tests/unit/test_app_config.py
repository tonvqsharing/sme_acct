"""C-1 regression: SECRET_KEY must exist outside TESTING."""

from __future__ import annotations

import pytest

from src.app import create_app


class TestSecretKeyPolicy:
    def test_missing_key_outside_testing_raises(self, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app()  # no config → not TESTING

    def test_testing_mode_allows_missing_key(self, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        app = create_app(config={"TESTING": True})
        assert app.config["TESTING"] is True

    def test_env_key_accepted(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "prod-value")
        app = create_app()
        assert app.config["SECRET_KEY"] == "prod-value"
