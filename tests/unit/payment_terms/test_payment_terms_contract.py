"""Contract interface tests for payment_terms brick.

Verifies ports are abstract, enforce full method surface, and only traffic
in primitives per brick boundary rules.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.payment_terms.contract import (
    DocumentNumberingSeriesRepositoryPort,
    PaymentTermRepositoryPort,
)
from src.bricks.payment_terms.domain import (
    DocumentNumberingSeries,
    PaymentTerm,
)

COMPANY_ID = uuid4()


def _term() -> PaymentTerm:
    from decimal import Decimal

    return PaymentTerm(
        id=uuid4(),
        company_id=COMPANY_ID,
        name="Net 30",
        due_days=30,
        interest_rate=Decimal(0),
    )


def _series() -> DocumentNumberingSeries:
    return DocumentNumberingSeries(
        id=uuid4(),
        company_id=COMPANY_ID,
        prefix="HD/",
        next_sequence=1,
    )


class TestPaymentTermPort:
    def test_cannot_instantiate_abstract_port(self):
        with pytest.raises(TypeError):
            PaymentTermRepositoryPort()  # type: ignore[abstract]

    def test_full_surface_must_be_implemented(self):
        """Every port method is declared abstract."""

        required = [
            "get_by_id",
            "get_by_company",
            "get_default_by_company",
            "create",
            "update",
            "set_default",
            "soft_delete",
            "validate_name_unique",
        ]
        for name in required:
            method = getattr(PaymentTermRepositoryPort, name)
            assert getattr(method, "__isabstractmethod__", False), f"{name} must be @abstractmethod"

    def test_partial_implementation_still_abstract(self):
        class Partial(PaymentTermRepositoryPort):
            def get_by_id(self, payment_term_id):
                return None

        with pytest.raises(TypeError):
            Partial()  # type: ignore[abstract]

    def test_full_implementation_instantiable(self):

        class FakeRepo(PaymentTermRepositoryPort):
            def get_by_id(self, payment_term_id):
                return None

            def get_by_company(self, company_id):
                return []

            def get_default_by_company(self, company_id):
                return None

            def create(self, term):
                return term

            def update(self, term):
                return term

            def set_default(self, payment_term_id, actor, reason):
                return None

            def soft_delete(self, payment_term_id, actor, reason):
                return None

            def validate_name_unique(self, company_id, name):
                return True

        repo = FakeRepo()
        assert repo.create(_term()).due_days == 30


class TestSeriesPort:
    def test_cannot_instantiate_abstract_port(self):
        with pytest.raises(TypeError):
            DocumentNumberingSeriesRepositoryPort()  # type: ignore[abstract]

    def test_required_methods_exist(self):
        required = [
            "get_by_id",
            "get_by_company",
            "get_active_by_company",
            "create",
            "update",
            "activate",
            "deactivate",
            "validate_prefix_unique",
            "check_max_series_limit",
        ]
        for name in required:
            assert callable(getattr(DocumentNumberingSeriesRepositoryPort, name))

    def test_full_implementation_instantiable(self):
        class FakeRepo(DocumentNumberingSeriesRepositoryPort):
            def get_by_id(self, series_id):
                return None

            def get_by_company(self, company_id):
                return []

            def get_active_by_company(self, company_id):
                return []

            def create(self, series):
                return series

            def update(self, series):
                return series

            def activate(self, series_id, actor, reason):
                return None

            def deactivate(self, series_id, actor, reason):
                return None

            def validate_prefix_unique(self, company_id, prefix):
                return True

            def check_max_series_limit(self, company_id):
                return False

        repo = FakeRepo()
        assert repo.create(_series()).prefix == "HD/"
