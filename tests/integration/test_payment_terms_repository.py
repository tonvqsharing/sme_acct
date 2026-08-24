"""Integration tests for payment_terms repositories — real SQLAlchemy + SQLite.

Repo adapters must satisfy contract ports against a real DB engine.
In-memory SQLite per TESTING_STRATEGY §5.3.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.payment_terms.domain import (
    DocumentNumberingSeries,
    PaymentTerm,
    PaymentTermStatus,
)
from src.bricks.payment_terms.storage import (
    Base,
    SQLAlchemyDocumentNumberingSeriesRepository,
    SQLAlchemyPaymentTermRepository,
)

COMPANY_A = uuid4()
COMPANY_B = uuid4()


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture()
def term_repo(session_factory):
    return SQLAlchemyPaymentTermRepository(session_factory())


@pytest.fixture()
def series_repo(session_factory):
    return SQLAlchemyDocumentNumberingSeriesRepository(session_factory())


def _term(company_id: UUID = COMPANY_A, name: str = "Net 30") -> PaymentTerm:
    return PaymentTerm(
        id=uuid4(),
        company_id=company_id,
        name=name,
        due_days=30,
        interest_rate=Decimal("1.5"),
    )


def _series(company_id: UUID = COMPANY_A, prefix: str = "HD/") -> DocumentNumberingSeries:
    return DocumentNumberingSeries(
        id=uuid4(),
        company_id=company_id,
        prefix=prefix,
        next_sequence=1,
    )


# ─── PaymentTermRepository ────────────────────────────────────────────────


class TestPaymentTermRepoRoundTrip:
    def test_create_then_get_by_id_preserves_fields(self, term_repo):
        created = term_repo.create(_term())
        loaded = term_repo.get_by_id(created.id)

        assert loaded is not None
        assert loaded.name == "Net 30"
        assert loaded.due_days == 30
        assert loaded.interest_rate == Decimal("1.5")
        assert loaded.status == PaymentTermStatus.ACTIVE
        assert loaded.is_default is False

    def test_get_unknown_returns_none(self, term_repo):
        assert term_repo.get_by_id(uuid4()) is None

    def test_get_by_company_is_tenant_isolated(self, term_repo):
        """Data isolation §16: company A never sees company B's terms."""
        term_repo.create(_term(COMPANY_A, "A-term"))
        term_repo.create(_term(COMPANY_B, "B-term"))

        ids_a = {t.name for t in term_repo.get_by_company(COMPANY_A)}
        assert ids_a == {"A-term"}


class TestPaymentTermDefaultSemantics:
    def test_set_default_clears_previous(self, term_repo):
        """R-001 at persistence layer: exactly one default per company."""
        t1 = term_repo.create(_term(name="first"))
        t2 = term_repo.create(_term(name="second"))

        term_repo.set_default(t1.id, uuid4(), "pick 1")
        assert term_repo.get_default_by_company(COMPANY_A).id == t1.id

        term_repo.set_default(t2.id, uuid4(), "switch to 2")
        current = term_repo.get_default_by_company(COMPANY_A)
        assert current.id == t2.id

        # Fresh read proves previous flag cleared in DB, not just in memory
        reloaded = term_repo.get_by_id(t1.id)
        assert reloaded.is_default is False

    def test_defaults_scoped_per_company(self, term_repo):
        t_a = term_repo.create(_term(COMPANY_A, "a"))
        t_b = term_repo.create(_term(COMPANY_B, "b"))
        term_repo.set_default(t_a.id, uuid4(), "r")
        term_repo.set_default(t_b.id, uuid4(), "r")

        assert term_repo.get_default_by_company(COMPANY_A).id == t_a.id
        assert term_repo.get_default_by_company(COMPANY_B).id == t_b.id


class TestPaymentTermUniquenessAndSoftDelete:
    def test_name_unique_within_company(self, term_repo):
        term_repo.create(_term(name="Net 15"))
        assert term_repo.validate_name_unique(COMPANY_A, "Net 30") is True
        assert term_repo.validate_name_unique(COMPANY_A, "Net 15") is False

    def test_name_unique_scoped_across_companies(self, term_repo):
        term_repo.create(_term(COMPANY_A, "Shared"))
        assert term_repo.validate_name_unique(COMPANY_B, "Shared") is True

    def test_soft_delete_preserves_row_and_uniqueness(self, term_repo):
        """R-006: row kept; name stays reserved (retention semantics)."""
        term = term_repo.create(_term(name="Legacy"))
        term_repo.soft_delete(term.id, uuid4(), "unused")

        stored = term_repo.get_by_id(term.id)
        assert stored.status == PaymentTermStatus.INACTIVE  # still there
        assert term_repo.validate_name_unique(COMPANY_A, "Legacy") is False

    def test_update_persists(self, term_repo):
        term = term_repo.create(_term())
        term.due_days = 45
        term.checksum = "a" * 64
        term_repo.update(term)

        loaded = term_repo.get_by_id(term.id)
        assert loaded.due_days == 45
        assert loaded.checksum == "a" * 64


# ─── Series repository ────────────────────────────────────────────────────


class TestSeriesRepoRoundTrip:
    def test_create_then_get_by_id(self, series_repo):
        created = series_repo.create(_series(prefix="PN/"))
        loaded = series_repo.get_by_id(created.id)

        assert loaded.prefix == "PN/"
        assert loaded.next_sequence == 1
        assert loaded.max_sequences == 999999
        assert loaded.is_active is True

    def test_increment_survives_session_boundary(self, series_repo, session_factory):
        """Atomic increment must persist beyond the adapter's session."""
        series = series_repo.create(_series())

        fresh_session = session_factory()
        fresh_repo = SQLAlchemyDocumentNumberingSeriesRepository(fresh_session)
        loaded = fresh_repo.get_by_id(series.id)
        loaded.increment_sequence()
        fresh_repo.update(loaded)

        reread = series_repo.get_by_id(series.id)
        assert reread.next_sequence == 2


class TestSeriesUniquenessAndLimits:
    def test_prefix_unique_within_company(self, series_repo):
        series_repo.create(_series(prefix="HD/"))
        assert series_repo.validate_prefix_unique(COMPANY_A, "PN/") is True
        assert series_repo.validate_prefix_unique(COMPANY_A, "HD/") is False

    def test_prefix_unique_scoped_across_companies(self, series_repo):
        series_repo.create(_series(COMPANY_A, "HD/"))
        assert series_repo.validate_prefix_unique(COMPANY_B, "HD/") is True

    def test_max_limit_at_15(self, series_repo):
        """R-008: cap counts ACTIVE series only."""
        for i in range(14):
            letters = f"{chr(65 + i // 26)}{chr(65 + i % 26)}/"
            series_repo.create(_series(prefix=letters))

        assert series_repo.check_max_series_limit(COMPANY_A) is False

        series_repo.create(_series(prefix="ZZ/"))
        assert series_repo.check_max_series_limit(COMPANY_A) is True

    def test_max_limit_ignores_deactivated(self, series_repo):
        for i in range(15):
            letters = f"{chr(65 + i // 26)}{chr(65 + i % 26)}/"
            series_repo.create(_series(prefix=letters))
        first = min(
            series_repo.get_active_by_company(COMPANY_A),
            key=lambda item: item.prefix,
        )
        series_repo.deactivate(first.id, uuid4(), "retire")

        assert series_repo.check_max_series_limit(COMPANY_A) is False

    def test_activate_deactivate_round_trip(self, series_repo):
        series = series_repo.create(_series())
        series_repo.deactivate(series.id, uuid4(), "pause")
        assert series_repo.get_by_id(series.id).is_active is False

        series_repo.activate(series.id, uuid4(), "resume")
        assert series_repo.get_by_id(series.id).is_active is True
