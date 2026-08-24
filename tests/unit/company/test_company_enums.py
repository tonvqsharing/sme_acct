"""Tests for Company domain enums."""

import pytest

from src.bricks.company.domain import (
    AccountingRegime,
    CompanyStatus,
    CompanyType,
    TaxId,
)


class TestCompanyType:
    """CompanyType enum tests per Luật Doanh nghiệp 2020 Art. 2."""

    def test_single_llc_value(self):
        assert CompanyType.SINGLE_LLC.value == "single_llc"

    def test_multi_llc_value(self):
        assert CompanyType.MULTI_LLC.value == "multi_llc"

    def test_jsc_value(self):
        assert CompanyType.JSC.value == "jsc"

    def test_listed_jsc_value(self):
        assert CompanyType.LISTED_JSC.value == "listed_jsc"

    def test_sole_prop_value(self):
        assert CompanyType.SOLE_PROP.value == "sole_prop"

    def test_partnership_value(self):
        assert CompanyType.PARTNERSHIP.value == "partnership"

    def test_household_value(self):
        assert CompanyType.HOUSEHOLD.value == "household"

    def test_coop_value(self):
        assert CompanyType.COOP.value == "coop"

    def test_all_types_exist(self):
        assert len(CompanyType) == 8


class TestCompanyStatus:
    """CompanyStatus enum tests."""

    def test_active_value(self):
        assert CompanyStatus.ACTIVE.value == "active"

    def test_suspended_value(self):
        assert CompanyStatus.SUSPENDED.value == "suspended"

    def test_dissolved_value(self):
        assert CompanyStatus.DISSOLVED.value == "dissolved"

    def test_all_statuses_exist(self):
        assert len(CompanyStatus) == 3


class TestAccountingRegime:
    """AccountingRegime enum tests per Circular 99/2025/TT-BTC."""

    def test_tt99_value(self):
        assert AccountingRegime.TT99.value == "tt99"

    def test_tt58_micro_value(self):
        assert AccountingRegime.TT58_MICRO.value == "tt58_micro"

    def test_tt133_value(self):
        assert AccountingRegime.TT133.value == "tt133"

    def test_all_regimes_exist(self):
        assert len(AccountingRegime) == 3

    def test_tt200_removed_as_outdated(self):
        """TT200 (200/2014) superseded by Circular 99/2025 — not selectable."""
        assert "TT200" not in AccountingRegime.__members__

    def test_tt132_2018_removed_as_outdated(self):
        """Siêu-nhỏ regime replaced by TT58/2026 eff 01/07/2026."""
        assert "TT132" not in AccountingRegime.__members__

    def test_regime_set_matches_law_as_of_2026_08(self):
        """Pin the full set — any addition/removal must cite a legal source."""
        assert {r.name for r in AccountingRegime} == {
            "TT99",
            "TT58_MICRO",
            "TT133",
        }


class TestTaxId:
    """TaxId value object tests per Mã số thuế format."""

    def test_valid_10_digit_mst(self):
        tax_id = TaxId("0123456789")
        assert tax_id.value == "0123456789"

    def test_valid_10_digit_with_3_digit_suffix(self):
        tax_id = TaxId("0123456789-001")
        assert tax_id.value == "0123456789-001"

    def test_invalid_too_short(self):
        with pytest.raises(ValueError, match="Invalid MST format"):
            TaxId("123456789")

    def test_invalid_letters(self):
        with pytest.raises(ValueError, match="Invalid MST format"):
            TaxId("012345678A")

    def test_invalid_suffix(self):
        with pytest.raises(ValueError, match="Invalid MST format"):
            TaxId("0123456789-00")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Invalid MST format"):
            TaxId("")

    def test_value_object_immutable(self):
        tax_id = TaxId("0123456789")
        with pytest.raises(AttributeError):
            tax_id.value = "9999999999"
