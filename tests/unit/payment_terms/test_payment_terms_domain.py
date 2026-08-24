"""Unit tests for payment_terms domain entities.

Pure domain logic — no DB, no Flask. Per docs/payment-terms/specs-payment-terms.md §3.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.payment_terms.domain import (
    DocumentNumberingSeries,
    PaymentTerm,
    PaymentTermStatus,
    SeriesStatus,
)

COMPANY_ID = uuid4()


# ─── PaymentTerm ───────────────────────────────────────────────────────────


class TestPaymentTermCreation:
    def test_create_minimal(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
        )
        assert term.name == "Net 30"
        assert term.due_days == 30
        assert term.is_default is False
        assert term.status == PaymentTermStatus.ACTIVE

    def test_created_at_defaults_to_today(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="Net 15",
            due_days=15,
            interest_rate=Decimal(0),
        )
        assert term.created_at == date.today()  # noqa: DTZ011 — test clock anchor

    def test_checksum_defaults_empty(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="Net 7",
            due_days=7,
            interest_rate=Decimal(0),
        )
        assert term.checksum == ""


class TestPaymentTermValidation:
    """R-002: due_days must be >= 1."""

    @pytest.mark.parametrize("due_days", [0, -1, -100])
    def test_due_days_below_one_rejected(self, due_days):
        with pytest.raises(ValueError, match="due_days"):
            PaymentTerm(
                id=uuid4(),
                company_id=COMPANY_ID,
                name="Bad",
                due_days=due_days,
                interest_rate=Decimal(0),
            )

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="name"):
            PaymentTerm(
                id=uuid4(),
                company_id=COMPANY_ID,
                name="",
                due_days=30,
                interest_rate=Decimal(0),
            )

    def test_name_over_200_chars_rejected(self):
        with pytest.raises(ValueError, match="name"):
            PaymentTerm(
                id=uuid4(),
                company_id=COMPANY_ID,
                name="X" * 201,
                due_days=30,
                interest_rate=Decimal(0),
            )

    def test_negative_interest_rate_rejected(self):
        with pytest.raises(ValueError, match="interest_rate"):
            PaymentTerm(
                id=uuid4(),
                company_id=COMPANY_ID,
                name="Net 30",
                due_days=30,
                interest_rate=Decimal("-0.01"),
            )


class TestPaymentTermDueDate:
    """R-012: due date = issue_date + due_days."""

    def test_calculate_due_date_net_30(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="Net 30",
            due_days=30,
            interest_rate=Decimal(0),
        )
        issue = date(2026, 8, 24)
        assert term.calculate_due_date(issue) == date(2026, 9, 23)

    def test_calculate_due_date_net_1(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="COD",
            due_days=1,
            interest_rate=Decimal(0),
        )
        issue = date(2026, 1, 31)
        assert term.calculate_due_date(issue) == date(2026, 2, 1)


# ─── DocumentNumberingSeries ───────────────────────────────────────────────


class TestSeriesPrefixValidation:
    """R-007: GDT Circular 163/2020/TT-BTC format ^[A-Z]{2,}/$."""

    @pytest.mark.parametrize("prefix", ["HD/", "PN/", "CV/", "PTBH/", "AB/"])
    def test_valid_prefixes_accepted(self, prefix):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix=prefix,
            next_sequence=1,
        )
        assert series.validate_prefix() is True

    @pytest.mark.parametrize(
        "prefix",
        [
            "hd/",  # lowercase
            "HD",  # missing slash
            "/",  # no letters
            "H/D/",  # slash inside
            "H1/",  # digit
            "H/",  # single letter
            "",  # empty
        ],
    )
    def test_invalid_prefixes_fail_validation(self, prefix):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix=prefix,
            next_sequence=1,
        )
        assert series.validate_prefix() is False

    def test_prefix_validator_is_pure_predicate(self):
        """Entity exposes validator; service layer raises EX-004 on failure."""
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="bad-prefix",
            next_sequence=1,
        )
        assert series.validate_prefix() is False


class TestSeriesIncrement:
    def test_increment_returns_new_sequence(self):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="HD/",
            next_sequence=1,
        )
        assert series.increment_sequence() == 2
        assert series.next_sequence == 2

    def test_can_increment_under_max(self):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="HD/",
            next_sequence=999998,
        )
        assert series.can_increment() is True

    def test_final_sequence_at_max_still_issuable(self):
        """next == max: last document number may be issued."""
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="HD/",
            next_sequence=999999,
        )
        assert series.can_increment() is True
        assert series.increment_sequence() == 1000000
        assert series.can_increment() is False

    def test_default_max_sequences(self):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="HD/",
            next_sequence=1,
        )
        assert series.max_sequences == 999999


class TestSeriesDefaults:
    def test_series_is_active_by_default(self):
        series = DocumentNumberingSeries(
            id=uuid4(),
            company_id=COMPANY_ID,
            prefix="HD/",
            next_sequence=1,
        )
        assert series.is_active is True
        assert series.status == SeriesStatus.ACTIVE

    def test_next_sequence_must_be_positive(self):
        with pytest.raises(ValueError, match="next_sequence"):
            DocumentNumberingSeries(
                id=uuid4(),
                company_id=COMPANY_ID,
                prefix="HD/",
                next_sequence=0,
            )

    def test_max_sequences_must_be_positive(self):
        with pytest.raises(ValueError, match="max_sequences"):
            DocumentNumberingSeries(
                id=uuid4(),
                company_id=COMPANY_ID,
                prefix="HD/",
                next_sequence=1,
                max_sequences=-5,
            )


# ─── Checksum chaining (R-010) ─────────────────────────────────────────────


class TestChecksumChaining:
    """SHA-256(prev + actor + timestamp + action + reason + entity_id), genesis '0'*64."""

    def test_genesis_checksum_is_64_zeros(self):
        from src.bricks.payment_terms.domain import GENESIS_CHECKSUM

        assert GENESIS_CHECKSUM == "0" * 64

    def test_compute_checksum_deterministic(self):
        from src.bricks.payment_terms.domain import compute_checksum

        actor = uuid4()
        entity = uuid4()
        ts = "2026-08-24T10:00:00"

        c1 = compute_checksum(
            prev="0" * 64,
            actor=actor,
            timestamp=ts,
            action="CREATE",
            reason="init",
            entity_id=entity,
        )
        c2 = compute_checksum(
            prev="0" * 64,
            actor=actor,
            timestamp=ts,
            action="CREATE",
            reason="init",
            entity_id=entity,
        )
        assert c1 == c2
        assert len(c1) == 64

    def test_compute_checksum_differs_on_any_field_change(self):
        from src.bricks.payment_terms.domain import compute_checksum

        base = {
            "prev": "0" * 64,
            "actor": uuid4(),
            "timestamp": "2026-08-24T10:00:00",
            "action": "CREATE",
            "reason": "init",
            "entity_id": uuid4(),
        }
        variants = [
            {**base, "prev": "1" * 64},
            {**base, "action": "UPDATE"},
            {**base, "reason": "other"},
            {**base, "actor": uuid4()},
        ]
        original = compute_checksum(**base)
        for v in variants:
            assert compute_checksum(**v) != original

    def test_chain_two_events(self):
        """Second event's checksum builds on first event's checksum."""
        from src.bricks.payment_terms.domain import compute_checksum

        entity = uuid4()
        first = compute_checksum(
            prev="0" * 64,
            actor=uuid4(),
            timestamp="2026-08-24T10:00:00",
            action="CREATE",
            reason="init",
            entity_id=entity,
        )
        second = compute_checksum(
            prev=first,
            actor=uuid4(),
            timestamp="2026-08-24T11:00:00",
            action="UPDATE",
            reason="fix",
            entity_id=entity,
        )
        assert second != first
        assert len(second) == 64


# ─── Immutability sanity ───────────────────────────────────────────────────


class TestTimedeltaUsage:
    def test_due_date_matches_timedelta_semantics(self):
        term = PaymentTerm(
            id=uuid4(),
            company_id=COMPANY_ID,
            name="Net 45",
            due_days=45,
            interest_rate=Decimal(0),
        )
        issue = date(2026, 3, 1)
        expected = issue + timedelta(days=45)
        assert term.calculate_due_date(issue) == expected
