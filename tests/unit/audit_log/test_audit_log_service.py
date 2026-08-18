# TDD: AuditLogService Unit Tests

"""Unit tests for AuditLogService - red-green-refactor methodology."""

import pytest
from uuid import UUID, uuid4
from datetime import date, datetime

from src.application.services.audit_log_service import AuditLogService
from src.application.ports import AuditLogRepositoryPort
from src.domain.exceptions import DomainException


class TestAuditLogServiceCreate:
    """Test creating audit records via AuditLogService."""

    def test_create_audit_record_happy_path(self, audit_log_service, sample_audit_record):
        """Happy path: create audit record with valid parameters."""
        # Act
        result = audit_log_service.create(**sample_audit_record)

        # Assert
        assert result is not None
        assert result["entity_type"] == sample_audit_record["entity_type"]
        assert result["entity_id"] == str(sample_audit_record["entity_id"])
        assert result["action"] == sample_audit_record["action"]
        assert result["actor_id"] == str(sample_audit_record["actor_id"])
        assert result["changed_at"] is not None
        # before_value and after_value should be None for CREATE action
        assert result.get("before_value") is None
        assert result.get("after_value") is None

    def test_create_audit_record_with_field_update(self, audit_log_service, sample_audit_record_update):
        """UPDATE action with field_name and before/after values."""
        # Act
        result = audit_log_service.create(**sample_audit_record_update)

        # Assert
        assert result is not None
        assert result["action"] == "UPDATE"
        assert result.get("field_name") == "vat_rate"
        assert result.get("before_value") == "0.10"
        assert result.get("after_value") == "0.15"

    def test_create_audit_record_invalid_entity_type(self, audit_log_service):
        """Invalid entity_type should raise validation error."""
        # Arrange
        invalid_record = {
            "entity_type": "NonExistent",
            "entity_id": uuid4(),
            "action": "CREATE",
            "actor_id": uuid4(),
        }

        # Act & Assert
        with pytest.raises(DomainException, match="Invalid entity_type"):
            audit_log_service.create(**invalid_record)

    def test_create_audit_record_invalid_action(self, audit_log_service):
        """Invalid action should raise validation error."""
        # Arrange
        invalid_record = {
            "entity_type": "Invoice",
            "entity_id": uuid4(),
            "action": "NONEXISTENT",
            "actor_id": uuid4(),
        }

        # Act & Assert
        with pytest.raises(DomainException, match="Invalid action"):
            audit_log_service.create(**invalid_record)

    def test_create_audit_record_missing_actor_id(self, audit_log_service):
        """Missing actor_id should raise validation error."""
        # Arrange
        incomplete_record = {
            "entity_type": "Invoice",
            "entity_id": uuid4(),
            "action": "CREATE",
            # actor_id missing
        }

        # Act & Assert
        with pytest.raises(DomainException, match="actor_id is required"):
            audit_log_service.create(**incomplete_record)


class TestAuditLogServiceValidation:
    """Test validation logic in AuditLogService."""

    def test_validate_entity_type_closed_enum(self, audit_log_service):
        """entity_type must be from closed enum."""
        # Valid entity types
        valid_types = ["Company", "Partner", "Invoice", "Voucher", "BankAccount", "Config"]
        for et in valid_types:
            result = audit_log_service.validate_entity_type(et)
            assert result is True

        # Invalid entity type
        with pytest.raises(DomainException, match="Invalid entity_type"):
            audit_log_service.validate_entity_type("NonExistent")

    def test_validate_action_closed_enum(self, audit_log_service):
        """action must be from closed enum."""
        # Valid actions
        valid_actions = ["CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "SUSPEND", "REACTIVATE", "DISSOLVE"]
        for action in valid_actions:
            result = audit_log_service.validate_action(action)
            assert result is True

        # Invalid action
        with pytest.raises(DomainException, match="Invalid action"):
            audit_log_service.validate_action("NONEXISTENT")

    def test_actor_id_must_be_uuid(self, audit_log_service):
        """actor_id must be a valid UUID."""
        # Valid UUID
        result = audit_log_service.validate_actor_id(uuid4())
        assert result is True

        # Invalid actor_id
        with pytest.raises(DomainException, match="actor_id must be a valid UUID"):
            audit_log_service.validate_actor_id("not-a-uuid")


# Conftest for test fixtures
@pytest.fixture
def audit_log_service():
    """Create AuditLogService instance for testing."""
    from src.infrastructure.repositories import SQLAlchemyAuditLogRepository
    repo = SQLAlchemyAuditLogRepository()
    from src.application.services.audit_log_service import AuditLogService
    service = AuditLogService(repo)
    return service


@pytest.fixture
def sample_audit_record():
    """Valid audit record for CREATE action."""
    return {
        "entity_type": "Invoice",
        "entity_id": uuid4(),
        "action": "CREATE",
        "actor_id": uuid4(),
    }


@pytest.fixture
def sample_audit_record_update():
    """Valid audit record for UPDATE action with field change."""
    return {
        "entity_type": "Invoice",
        "entity_id": uuid4(),
        "action": "UPDATE",
        "field_name": "vat_rate",
        "before_value": "0.10",
        "after_value": "0.15",
        "actor_id": uuid4(),
    }# Conftest for test fixtures
@pytest.fixture
def audit_log_service():
    """Create AuditLogService instance for testing."""
    from src.infrastructure.repositories import SQLAlchemyAuditLogRepository
    repo = SQLAlchemyAuditLogRepository()
    from src.application.services.audit_log_service import AuditLogService
    service = AuditLogService(repo)
    return service


@pytest.fixture
def sample_audit_record():
    """Valid audit record for CREATE action."""
    return {
        "entity_type": "Invoice",
        "entity_id": uuid4(),
        "action": "CREATE",
        "actor_id": uuid4(),
    }


@pytest.fixture
def sample_audit_record_update():
    """Valid audit record for UPDATE action with field change."""
    return {
        "entity_type": "Invoice",
        "entity_id": uuid4(),
        "action": "UPDATE",
        "field_name": "vat_rate",
        "before_value": "0.10",
        "after_value": "0.15",
        "actor_id": uuid4(),
    }


class TestAuditLogServiceDestruction:
    """Test Certificate of Destruction functionality per Luật Kế toán 2015.

    Records must be retained for minimum 10 years before destruction.
    """

    def test_verify_destruction_eligibility_happy_path(self, audit_log_service):
        """Record older than 10 years should be eligible for destruction."""
        from datetime import date
        old_date = (date.today().replace(year=date.today().year - 11)).isoformat()

        result = audit_log_service.verify_destruction_eligibility(
            record_id=uuid4(),
            changed_at=old_date
        )

        assert result["eligible"] is True
        assert result["years_elapsed"] >= 10
        assert result["reason"] is None

    def test_verify_destruction_eligibility_too_young(self, audit_log_service):
        """Record younger than 10 years should NOT be eligible."""
        young_date = (date.today().replace(year=date.today().year - 5)).isoformat()

        result = audit_log_service.verify_destruction_eligibility(
            record_id=uuid4(),
            changed_at=young_date
        )

        assert result["eligible"] is False
        assert result["years_elapsed"] == 5
        assert result["reason"] is not None

    def test_verify_destruction_eligibility_exactly_10_years(self, audit_log_service):
        """Record exactly 10 years old should be eligible."""
        exactly_10 = (date.today().replace(year=date.today().year - 10)).isoformat()

        result = audit_log_service.verify_destruction_eligibility(
            record_id=uuid4(),
            changed_at=exactly_10
        )

        assert result["eligible"] is True
        assert result["years_elapsed"] == 10

    def test_verify_destruction_eligibility_invalid_date(self, audit_log_service):
        """Invalid date format should return not eligible."""
        result = audit_log_service.verify_destruction_eligibility(
            record_id=uuid4(),
            changed_at="not-a-date"
        )

        assert result["eligible"] is False
        assert result["reason"] is not None
        assert "invalid_date_format" in result["reason"]

    def test_destroy_records_success(self, audit_log_service):
        """Destroy records should return success result."""
        record_ids = [uuid4() for _ in range(3)]
        result = audit_log_service.destroy_records(record_ids, uuid4())

        assert result["destroyed_count"] == 3
        assert result["failed_ids"] == []
        assert result["reason"] is None

    def test_destroy_records_empty_list(self, audit_log_service):
        """Destroy with empty list should return 0 destroyed."""
        result = audit_log_service.destroy_records([], uuid4())

        assert result["destroyed_count"] == 0
        assert result["failed_ids"] == []
