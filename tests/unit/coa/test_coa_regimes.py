"""Regime-aware COA calibration — TT133 (3-4 digit) vs TT99 (10-digit spec).

Spec source: docs/coa/specs-coa-module-2026.md §Value Objects (AccountCode).
Law source: mof.gov.vn/vbpl.vn as of 2026-08 (TT99/2025, TT58/2026, TT133/2016).
"""

from __future__ import annotations

import pytest

from src.bricks.coa.domain import Account
from src.bricks.coa.services import (
    AccountService,
    ParentNotFoundError,
)


class FakeRepo:
    def __init__(self):
        self.accounts = {}

    def create(self, acc):
        self.accounts[(str(acc.company_id), acc.code)] = acc
        return acc

    def get_by_code(self, company_id, code):
        return self.accounts.get((str(company_id), code))

    def get_by_company(self, company_id):
        return [a for k, a in self.accounts.items() if k[0] == str(company_id)]

    def update(self, acc):
        self.accounts[(str(acc.company_id), acc.code)] = acc
        return acc

    def validate_code_unique(self, company_id, code):
        return (str(company_id), code) not in self.accounts


C = "99999999-8888-7777-6666-555555555555"


# ─── Seam 1: entity validation per regime ──────────────────────────────────


class TestTT99TenDigitCodes:
    r"""2026 COA spec: ^[1-9]\d{2}\d{3}\d{3}(-\d{1,3})?$"""

    def test_ten_digit_code_accepted(self):
        acc = Account(company_id=C, code="1311000001", name="Phải thu KH A", regime="tt99")
        assert acc.is_detail is True

    def test_ten_digit_with_suffix_accepted(self):
        acc = Account(
            company_id=C,
            code="3331100001-001",
            name="VAT nhóm A",
            regime="tt99",
        )
        assert acc.is_detail is True

    @pytest.mark.parametrize("bad", ["1311", "131", "131100001", "0311000001"])
    def test_short_or_malformed_rejected_under_tt99(self, bad):
        with pytest.raises(ValueError, match="code"):
            Account(company_id=C, code=bad, name="X", regime="tt99")

    def test_aggregate_prefixes_are_not_detail(self):
        base = Account(company_id=C, code="1310000000", name="AR base", regime="tt99")
        mid = Account(company_id=C, code="1311000000", name="AR sub", regime="tt99")
        assert base.is_detail is False
        assert mid.is_detail is False


class TestTT133ShortCodes:
    def test_four_digit_still_valid_under_tt133(self):
        acc = Account(company_id=C, code="1311", name="PTKH", regime="tt133")
        assert acc.is_detail is True

    def test_default_regime_is_tt133(self):
        acc = Account(company_id=C, code="111", name="Tiền mặt")
        assert acc.regime == "tt133"

    def test_ten_digit_rejected_under_tt133(self):
        with pytest.raises(ValueError, match="code"):
            Account(company_id=C, code="1311000001", name="X", regime="tt133")


# ─── Seam 2: service hierarchy rules per regime ────────────────────────────


@pytest.fixture()
def svc():
    return AccountService(FakeRepo())


class TestHierarchyPerRegime:
    def test_tt99_parent_group_boundaries(self, svc):
        svc.create_account(
            C,
            "1310000000",
            "AR aggregate",
            regime="tt99",
            actor="u",
            reason="r",
        )
        child = svc.create_account(
            C,
            "1311000001",
            "Customer A",
            parent_code="1310000000",
            regime="tt99",
            actor="u",
            reason="r",
        )
        assert child.is_detail is True

    def test_tt99_bad_parent_length_rejected(self, svc):
        with pytest.raises(ParentNotFoundError):
            svc.create_account(
                C,
                "1311000001",
                "Orphan",
                parent_code="131",
                regime="tt99",
                actor="u",
                reason="r",
            )

    def test_tt133_still_enforces_short_catalog(self, svc):
        """5-digit codes are foreign to the TT133 catalog entirely."""
        with pytest.raises(ValueError, match="Invalid account code"):
            svc.create_account(
                C,
                "11211",
                "deep",
                regime="tt133",
                actor="u",
                reason="r",
            )

    def test_tt133_detail_under_aggregate_ok(self, svc):
        svc.create_account(C, "112", "TG NH", regime="tt133", actor="u", reason="r")
        child = svc.create_account(
            C,
            "1121",
            "VTB",
            parent_code="112",
            regime="tt133",
            actor="u",
            reason="r",
        )
        assert child.is_detail is True


# ─── Seam 3: chart template resolution ─────────────────────────────────────


class TestChartTemplate:
    def test_tt133_roles_resolve_to_native_codes(self):
        from src.bricks.coa.domain import resolve_chart_role

        assert resolve_chart_role("ar", "tt133") == "1311"
        assert resolve_chart_role("revenue", "tt133") == "5111"
        assert resolve_chart_role("vat_output", "tt133") == "3331"

    def test_tt99_roles_resolve_to_spec_10_digit(self):
        from src.bricks.coa.domain import resolve_chart_role

        ar = resolve_chart_role("ar", "tt99")
        rev = resolve_chart_role("revenue", "tt99")
        vat = resolve_chart_role("vat_output", "tt99")
        for code in (ar, rev, vat):
            assert len(code) == 10 and code[0] != "0"
        assert ar.startswith("131")
        assert rev.startswith("511")
        assert vat.startswith("3331")

    def test_tt58_micro_falls_back_to_tt133_catalog(self):
        from src.bricks.coa.domain import resolve_chart_role

        assert resolve_chart_role("ar", "tt58_micro") == "1311"

    def test_unknown_role_raises(self):
        from src.bricks.coa.domain import resolve_chart_role

        with pytest.raises(ValueError, match="role"):
            resolve_chart_role("nonexistent", "tt133")
