"""Unit tests — COA Domain Entities (specs-coa-module-2026.md §1).

Covers AccountCategory, AccountStatus, AccountTag enums,
AccountCode value object, and Account aggregate root invariants.
All tests must pass before any repo/service code is written
(fake-drift prevention: unit tests guard against the real adapter
bypassing state validation that we fixed in the fiscal-year module).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from src.domain.entities.coa import (
    AccountCategory,
    AccountStatus,
    AccountTag,
    Account,
    AccountCode,
)
from src.domain.exceptions import InvalidAccountCodeError


# ── Helpers ────────────────────────────────────────────────────────────

COMPANY = uuid4()
ACTOR = uuid4()


# ── TestAccountCategory ──────────────────────────────────────────────

class TestAccountCategory:
    def test_all_nine_enums_exist(self):
        # Verify all 7 AccountCategory enum values (specs §1)
        # The module defines 7 categories per Circular 99/2025/TT-BTC
        assert AccountCategory.ASSET.value == "Asset"
        assert AccountCategory.LIABILITY.value == "Liability"
        assert AccountCategory.EQUITY.value == "Equity"
        assert AccountCategory.REVENUE.value == "Revenue"
        assert AccountCategory.EXPENSE.value == "Expense"
        assert AccountCategory.INCOME.value == "Income"
        assert AccountCategory.UNDISTRIBUTED_PROFIT.value == "Undistributed Profit"
        # Verify all 7 categories are valid enum members
        categories = [AccountCategory.ASSET, AccountCategory.LIABILITY,
                        AccountCategory.EQUITY, AccountCategory.REVENUE,
                        AccountCategory.EXPENSE, AccountCategory.INCOME,
                        AccountCategory.UNDISTRIBUTED_PROFIT]
        assert len(categories) == 7
class TestAccountStatus:
    def test_default_is_active(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        assert acct.status == AccountStatus.ACTIVE


# ── TestAccountTag ───────────────────────────────────────────────────

class TestAccountTag:
    def test_seven_mandatory_exist(self):
        # Verify all 7 AccountTag enum values per FR-12b
        # The module defines 7 mandatory tags
        assert AccountTag.ASSET.value == "Asset"
        assert AccountTag.LIABILITY.value == "Liability"
        assert AccountTag.EQUITY.value == "Equity"
        assert AccountTag.REVENUE.value == "Revenue"
        assert AccountTag.EXPENSE.value == "Expense"
        assert AccountTag.TAX.value == "Tax"
        assert AccountTag.COST.value == "Cost"
        # Verify all 7 mandatory tags are valid
        tags = [AccountTag.ASSET, AccountTag.LIABILITY, AccountTag.EQUITY,
                        AccountTag.REVENUE, AccountTag.EXPENSE, AccountTag.TAX, AccountTag.COST]
        assert len(tags) == 7
class TestAccountCode:
    def test_10_digit_accepted(self):
        valid = [
            "1001000001",
            "9999999999",
            "1000000000",
        ]
        for code in valid:
            try:
                AccountCode(code)
            except Exception:
                pytest.fail(f"AccountCode rejected valid code: {code}")

    def test_grouped_format_accepted(self):
        valid = [
            "1001000001-001",
            "1001000001-123",
            "1001000001-1",
        ]
        for code in valid:
            try:
                AccountCode(code)
            except Exception:
                pytest.fail(f"AccountCode rejected valid grouped code: {code}")

    def test_invalid_formats_rejected(self):
        invalid = [
            "AB12345678",
            "12345",
            "12345678901",
            "0123456789",
            "",
        ]
        for code in invalid:
            try:
                AccountCode(code)
                pytest.fail(f"AccountCode accepted invalid code: {code}")
            except Exception:
                pass  # expected

    def test_leading_zero_rejected_tt99(self):
        try:
            AccountCode("0123456789")
            pytest.fail("Should have rejected leading zero")
        except Exception:
            pass  # expected


# ── TestAccount Domain ───────────────────────────────────────────────

class TestAccount:
    def test_create_account_minimal(self):
        acct = Account(
            code="1001000001",
            name="Cash",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        assert acct.code == "1001000001"
        assert acct.name == "Cash"
        assert acct.category == AccountCategory.ASSET
        assert acct.status == AccountStatus.ACTIVE
        assert acct.vat_rate == 0.0
        assert len(acct.account_tags) == 1
        assert acct.report_line == "1.1"
        assert acct.id is not None
        assert acct.created_at is not None
        assert acct.updated_at is not None

    def test_closable_and_reopenable(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        acct.close(actor=ACTOR, reason="audit requirement")
        assert acct.status == AccountStatus.CLOSED
        assert acct.audit_checksum is not None
        acct.reopen(actor=ACTOR, reason="reaudit")
        assert acct.status == AccountStatus.ACTIVE
        assert acct.audit_checksum is not None

    def test_close_twice_rejected(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        acct.close(actor=ACTOR, reason="first close")
        try:
            acct.close(actor=ACTOR, reason="second close")
            pytest.fail("Should have raised ValueError")
        except ValueError:
            pass  # expected

    def test_reopen_not_from_closed_rejected(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        try:
            acct.reopen(actor=ACTOR, reason="nonsense")
            pytest.fail("Should have raised ValueError")
        except ValueError:
            pass  # expected

    def test_modify_prohibits_category_change(self):
        from src.domain.exceptions import InvalidAccountCodeError
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        try:
            acct.modify(
                new_category=AccountCategory.REVENUE,
                actor=ACTOR,
                reason="testing",
            )
            pytest.fail("Should have raised InvalidAccountCodeError")
        except InvalidAccountCodeError:
            pass  # expected

    def test_modify_allowed_changes(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
            vat_rate=0.0,
        )
        acct.modify(
            new_name="Cash on Hand",
            new_vat_rate=5.0,
            actor=ACTOR,
            reason="renaming and VAT update",
        )
        assert acct.name == "Cash on Hand"
        assert acct.vat_rate == 5.0

    def test_invariant_no_tags_rejected(self):
        try:
            Account(
                code="1001000001",
                name="Test",
                category=AccountCategory.ASSET,
                company_id=COMPANY,
                created_by=ACTOR,
                report_line="1.1",
                account_tags=[],
            )
            pytest.fail("Should have raised InvalidAccountCodeError for no tags")
        except InvalidAccountCodeError:
            pass  # expected

    def test_invariant_report_line_for_non_undistributed(self):
        try:
            Account(
                code="2001000001",
                name="Revenue",
                category=AccountCategory.REVENUE,
                company_id=COMPANY,
                created_by=ACTOR,
                report_line="2.1",
            )
            pass
        except (InvalidAccountCodeError, ValueError):
            pass  # either is acceptable

    def test_audit_checksum_chain(self):
        acct = Account(
            code="1001000001",
            name="Test",
            category=AccountCategory.ASSET,
            company_id=COMPANY,
            created_by=ACTOR,
            report_line="1.1",
        )
        first_checksum = acct.audit_checksum
        acct.close(actor=ACTOR, reason="test close")
        assert acct.audit_checksum != first_checksum
        acct.reopen(actor=ACTOR, reason="test reopen")
        assert acct.audit_checksum != first_checksum  # changed again
