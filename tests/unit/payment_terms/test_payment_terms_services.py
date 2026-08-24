"""Unit tests for PaymentTermService & DocumentNumberingSeriesService.

Business rules R-001..R-012 + exception paths EX-001..EX-010.
Fake in-memory repo — no DB.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.bricks.payment_terms.contract import (
    DocumentNumberingSeriesRepositoryPort,
    PaymentTermRepositoryPort,
)
from src.bricks.payment_terms.domain import (
    GENESIS_CHECKSUM,
    DocumentNumberingSeries,
    PaymentTerm,
    PaymentTermStatus,
    SeriesStatus,
)
from src.bricks.payment_terms.services import (
    ActorRequiredError,
    DefaultAlreadyExistsError,
    DocumentNumberingSeriesService,
    DuplicatePaymentTermError,
    InvalidSeriesPrefixError,
    MaxSeriesExceededError,
    PaymentTermNotFoundError,
    PaymentTermService,
    PrefixAlreadyExistsError,
    ReasonRequiredError,
    SequenceAtMaxError,
    SeriesInactiveError,
    SeriesNotFoundError,
)

COMPANY = uuid4()
ACTOR_A = uuid4()  # "chief"
ACTOR_B = uuid4()  # second actor


# ─── Fakes ─────────────────────────────────────────────────────────────────


class FakePaymentTermRepo(PaymentTermRepositoryPort):
    def __init__(self):
        self.terms: dict[UUID, PaymentTerm] = {}

    def get_by_id(self, payment_term_id):
        return self.terms.get(payment_term_id)

    def get_by_company(self, company_id):
        return [t for t in self.terms.values() if t.company_id == company_id]

    def get_default_by_company(self, company_id):
        for t in self.terms.values():
            if t.company_id == company_id and t.is_default:
                return t
        return None

    def create(self, term):
        self.terms[term.id] = term
        return term

    def update(self, term):
        self.terms[term.id] = term
        return term

    def set_default(self, payment_term_id, actor, reason):
        term = self.terms.get(payment_term_id)
        if term is None:
            return None
        for other in self.terms.values():
            if other.company_id == term.company_id:
                other.is_default = False
        term.is_default = True
        return term

    def soft_delete(self, payment_term_id, actor, reason):
        term = self.terms.get(payment_term_id)
        if term:
            term.status = PaymentTermStatus.INACTIVE

    def validate_name_unique(self, company_id, name):
        return not any(t.company_id == company_id and t.name == name for t in self.terms.values())


class FakeSeriesRepo(DocumentNumberingSeriesRepositoryPort):
    MAX_ACTIVE = 15

    def __init__(self):
        self.series: dict[UUID, DocumentNumberingSeries] = {}

    def get_by_id(self, series_id):
        return self.series.get(series_id)

    def get_by_company(self, company_id):
        return [s for s in self.series.values() if s.company_id == company_id]

    def get_active_by_company(self, company_id):
        return [s for s in self.series.values() if s.company_id == company_id and s.is_active]

    def create(self, series):
        self.series[series.id] = series
        return series

    def update(self, series):
        self.series[series.id] = series
        return series

    def activate(self, series_id, actor, reason):
        series = self.series.get(series_id)
        if series is None:
            return None
        series.is_active = True
        series.status = SeriesStatus.ACTIVE
        return series

    def deactivate(self, series_id, actor, reason):
        series = self.series.get(series_id)
        if series is None:
            return None
        series.is_active = False
        series.status = SeriesStatus.INACTIVE
        return series

    def validate_prefix_unique(self, company_id, prefix):
        return not any(
            s.company_id == company_id and s.prefix == prefix for s in self.series.values()
        )

    def check_max_series_limit(self, company_id):
        return len(self.get_active_by_company(company_id)) >= self.MAX_ACTIVE


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def term_repo():
    return FakePaymentTermRepo()


@pytest.fixture()
def series_repo():
    return FakeSeriesRepo()


@pytest.fixture()
def pt_service(term_repo):
    return PaymentTermService(term_repo)


@pytest.fixture()
def dn_service(series_repo):
    return DocumentNumberingSeriesService(series_repo)


# ═══ PaymentTermService ════════════════════════════════════════════════════


class TestCreatePaymentTerm:
    def test_create_success_returns_active_term(self, pt_service):
        term = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="init setup",
        )
        assert term.name == "Net 30"
        assert term.due_days == 30
        assert term.status == PaymentTermStatus.ACTIVE
        assert term.is_default is False

    def test_create_stamps_genesis_checksum(self, pt_service):
        """R-010: first event chains from GENESIS_CHECKSUM."""
        term = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 15",
            due_days=15,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="init",
        )
        assert len(term.checksum) == 64
        assert term.checksum != GENESIS_CHECKSUM

    def test_create_duplicate_name_raises_EX002(self, pt_service):
        """EX-002 / AP-001."""
        pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="first",
        )
        with pytest.raises(DuplicatePaymentTermError):
            pt_service.create_payment_term(
                company_id=COMPANY,
                name="Net 30",
                due_days=45,
                interest_rate=Decimal(0),
                actor=ACTOR_A,
                reason="dup",
            )

    def test_same_name_ok_for_different_company(self, pt_service):
        """Uniqueness scoped per company (tenant isolation)."""
        other_company = uuid4()
        pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="a",
        )
        term = pt_service.create_payment_term(
            company_id=other_company,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="b",
        )
        assert term.company_id == other_company

    @pytest.mark.parametrize("bad_actor", [None, ""])
    def test_missing_actor_raises_EX001(self, pt_service, bad_actor):
        """EX-001."""
        with pytest.raises(ActorRequiredError):
            pt_service.create_payment_term(
                company_id=COMPANY,
                name="X",
                due_days=1,
                interest_rate=Decimal(0),
                actor=bad_actor,
                reason="r",
            )

    @pytest.mark.parametrize("bad_reason", [None, "", "   "])
    def test_blank_reason_rejected_R004(self, pt_service, bad_reason):
        with pytest.raises(ReasonRequiredError):
            pt_service.create_payment_term(
                company_id=COMPANY,
                name="X",
                due_days=1,
                interest_rate=Decimal(0),
                actor=ACTOR_A,
                reason=bad_reason,
            )


class TestSetDefault:
    """R-001: only one default per company; AP-003: block if exists."""

    def _make_two_terms(self, pt_service):
        t1 = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 15",
            due_days=15,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="t1",
        )
        t2 = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="t2",
        )
        return t1, t2

    def test_set_default_first_time_succeeds(self, pt_service):
        t1, _ = self._make_two_terms(pt_service)
        result = pt_service.set_default_payment_term(t1.id, ACTOR_A, "pick t1")
        assert result.is_default is True

    def test_set_default_when_exists_raises_EX003(self, pt_service):
        """EX-003 / AP-003: must deactivate existing default first."""
        t1, t2 = self._make_two_terms(pt_service)
        pt_service.set_default_payment_term(t1.id, ACTOR_A, "first")
        with pytest.raises(DefaultAlreadyExistsError):
            pt_service.set_default_payment_term(t2.id, ACTOR_A, "second")

    def test_set_default_on_missing_term_raises_not_found(self, pt_service):
        with pytest.raises(PaymentTermNotFoundError):
            pt_service.set_default_payment_term(uuid4(), ACTOR_A, "ghost")


class TestUpdateAndDeactivate:
    def test_update_changes_fields_and_chains_checksum(self, pt_service):
        term = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="c",
        )
        old_checksum = term.checksum
        updated = pt_service.update_payment_term(
            term.id,
            actor=ACTOR_B,
            reason="extend terms",
            due_days=45,
        )
        assert updated.due_days == 45
        assert updated.checksum != old_checksum

    def test_deactivate_is_soft_R006(self, pt_service):
        """R-006: row preserved, status flips — no deletion."""
        term = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Old",
            due_days=5,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="c",
        )
        result = pt_service.deactivate_payment_term(term.id, ACTOR_A, "unused")
        assert result.status == PaymentTermStatus.INACTIVE
        # Still retrievable — retention
        assert pt_service.get_payment_term(term.id) is not None

    def test_cannot_deactivate_the_default(self, pt_service):
        term = pt_service.create_payment_term(
            company_id=COMPANY,
            name="Default",
            due_days=10,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="c",
        )
        pt_service.set_default_payment_term(term.id, ACTOR_A, "set")
        with pytest.raises(DefaultAlreadyExistsError):
            pt_service.deactivate_payment_term(term.id, ACTOR_A, "oops")


class TestQueries:
    def test_list_by_company_filters_status(self, pt_service):
        active = pt_service.create_payment_term(
            company_id=COMPANY,
            name="A",
            due_days=1,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="a",
        )
        pt_service.create_payment_term(
            company_id=COMPANY,
            name="B",
            due_days=2,
            interest_rate=Decimal(0),
            actor=ACTOR_A,
            reason="b",
        )
        pt_service.deactivate_payment_term(active.id, ACTOR_A, "off")

        all_terms = pt_service.list_by_company(COMPANY)
        active_only = pt_service.list_by_company(COMPANY, status="active")
        assert len(all_terms) == 2  # retention: inactive still listed
        assert len(active_only) == 1

    def test_get_default_returns_none_when_unset(self, pt_service):
        assert pt_service.get_default(COMPANY) is None


# ═══ DocumentNumberingSeriesService ════════════════════════════════════════


def _letter_prefix(n: int) -> str:
    """n-th distinct valid GDT prefix: AA/, AB/, ..., AZ/, BA/ ..."""
    return f"{chr(65 + n // 26)}{chr(65 + n % 26)}/"


class TestCreateSeries:
    def test_create_valid_prefix_succeeds(self, dn_service):
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="init",
        )
        assert series.prefix == "HD/"
        assert series.next_sequence == 1
        assert series.is_active is True

    @pytest.mark.parametrize("bad_prefix", ["hd/", "HD", "/", "H/", "H1/"])
    def test_invalid_prefix_raises_EX004(self, dn_service, bad_prefix):
        """EX-004 / R-007."""
        with pytest.raises(InvalidSeriesPrefixError):
            dn_service.create_series(
                company_id=COMPANY,
                prefix=bad_prefix,
                actor=ACTOR_A,
                reason="x",
            )

    def test_duplicate_prefix_raises_AP002(self, dn_service):
        """AP-002 / R-009."""
        dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="1st",
        )
        with pytest.raises(PrefixAlreadyExistsError):
            dn_service.create_series(
                company_id=COMPANY,
                prefix="HD/",
                actor=ACTOR_A,
                reason="2nd",
            )

    def test_max_15_active_series_raises_EX005(self, dn_service):
        """EX-005 / R-008: GDT Circular 163 cap."""
        for i in range(15):
            dn_service.create_series(
                company_id=COMPANY,
                prefix=_letter_prefix(i),
                actor=ACTOR_A,
                reason=f"s{i}",
            )
        with pytest.raises(MaxSeriesExceededError):
            dn_service.create_series(
                company_id=COMPANY,
                prefix="ZZZ/",
                actor=ACTOR_A,
                reason="16th",
            )


class TestIncrementSequence:
    """R-010 atomic increment; EX-006/EX-008 guards; HP-004 flow."""

    def test_increment_returns_sequence_number(self, dn_service):
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        seq = dn_service.increment_sequence(series.id, ACTOR_A, "invoice")
        assert seq == 1
        fresh = dn_service.get_series(series.id)
        assert fresh.next_sequence == 2

    def test_document_number_format_HP004(self, dn_service):
        """HP-004: document number = prefix + sequence."""
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        seq = dn_service.increment_sequence(series.id, ACTOR_A, "invoice")
        assert f"{series.prefix}{seq:06d}" == "HD/000001"

    def test_increment_on_inactive_raises_EX008(self, dn_service):
        """EX-008 / AP-007."""
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        dn_service.deactivate_series(series.id, ACTOR_A, "pause")
        with pytest.raises(SeriesInactiveError):
            dn_service.increment_sequence(series.id, ACTOR_A, "invoice")

    def test_increment_at_max_raises_EX006(self, dn_service, series_repo):
        """EX-006 / AP-004."""
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        series.max_sequences = 3
        series_repo.update(series)
        for _ in range(3):  # issue sequences 1..3
            dn_service.increment_sequence(series.id, ACTOR_A, "fill")
        with pytest.raises(SequenceAtMaxError):
            dn_service.increment_sequence(series.id, ACTOR_A, "over")

    def test_increment_chains_checksum_each_time(self, dn_service):
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        first = series.checksum
        dn_service.increment_sequence(series.id, ACTOR_B, "inv 1")
        second = dn_service.get_series(series.id).checksum
        assert second != first

    def test_increment_missing_series_raises(self, dn_service):
        with pytest.raises(SeriesNotFoundError):
            dn_service.increment_sequence(uuid4(), ACTOR_A, "ghost")


class TestActivateDeactivateSeries:
    def test_activate_after_deactivate(self, dn_service):
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="PN/",
            actor=ACTOR_A,
            reason="i",
        )
        dn_service.deactivate_series(series.id, ACTOR_A, "pause")
        result = dn_service.activate_series(series.id, ACTOR_A, "resume")
        assert result.is_active is True

    def test_activate_blocked_at_max_limit_EX005(self, dn_service, series_repo):
        """EX-005: reactivating 16th active series blocked."""
        # Create 16 series (cap checked at create → use cap-1 + deactivated one)
        first = dn_service.create_series(
            company_id=COMPANY,
            prefix="HD/",
            actor=ACTOR_A,
            reason="i",
        )
        dn_service.deactivate_series(first.id, ACTOR_A, "pause")
        for i in range(dn_service.MAX_ACTIVE_SERIES):
            dn_service.create_series(
                company_id=COMPANY,
                prefix=_letter_prefix(i),
                actor=ACTOR_A,
                reason=f"f{i}",
            )
        assert len(series_repo.get_active_by_company(COMPANY)) == (dn_service.MAX_ACTIVE_SERIES)
        with pytest.raises(MaxSeriesExceededError):
            dn_service.activate_series(first.id, ACTOR_B, "resume")

    def test_deactivate_soft_only(self, dn_service):
        series = dn_service.create_series(
            company_id=COMPANY,
            prefix="CV/",
            actor=ACTOR_A,
            reason="i",
        )
        dn_service.deactivate_series(series.id, ACTOR_A, "retire")
        stored = dn_service.get_series(series.id)
        assert stored is not None  # R-011: never deleted
        assert stored.is_active is False
