"""Tests for app factory — create_app creates working Flask app."""

from __future__ import annotations

import pytest

from src.app import create_app


@pytest.fixture()
def app():
    """Create test app with in-memory SQLite."""
    return create_app({"TESTING": True})


@pytest.fixture()
def client(app):
    return app.test_client()


class TestCreateApp:
    def test_app_is_created(self, app):
        assert app is not None

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"

    def test_company_blueprint_registered(self, app):
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/api/v1/companies" in rules

    def test_company_list_endpoint(self, client):
        resp = client.get("/api/v1/companies")
        # 302 redirect to /login (unauthenticated) or 401
        assert resp.status_code in (401, 302)
