"""Tests for Company contract interface."""

from abc import ABC

import pytest

from src.bricks.company.contract import CompanyRepositoryPort


class TestCompanyRepositoryPort:
    """CompanyRepositoryPort interface tests."""

    def test_is_abstract_class(self):
        assert issubclass(CompanyRepositoryPort, ABC)

    def test_has_create_method(self):
        assert hasattr(CompanyRepositoryPort, "create")

    def test_has_get_by_id_method(self):
        assert hasattr(CompanyRepositoryPort, "get_by_id")

    def test_has_get_by_mst_method(self):
        assert hasattr(CompanyRepositoryPort, "get_by_mst")

    def test_has_list_active_method(self):
        assert hasattr(CompanyRepositoryPort, "list_active")

    def test_has_update_method(self):
        assert hasattr(CompanyRepositoryPort, "update")

    def test_has_deactivate_method(self):
        assert hasattr(CompanyRepositoryPort, "deactivate")

    def test_has_list_subsidiaries_method(self):
        assert hasattr(CompanyRepositoryPort, "list_subsidiaries")

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            CompanyRepositoryPort()
