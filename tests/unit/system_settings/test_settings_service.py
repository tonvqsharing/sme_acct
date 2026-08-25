"""Unit tests — SystemSettingsService per docs/tax-engine/specs §2-§3."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.system_settings.domain import (
    FlagLockedError,
    InvalidRegimeError,
    TaxRate,
)
from src.bricks.system_settings.services import (
    DuplicateSeriesPrefixError,
    MaxSeriesExceededError,
    SodViolationError,
    SystemSettingsService,
)

COMPANY = uuid4()
ADMIN = uuid4()
CHIEF = uuid4()


class FakeRepo:
    def __init__(self):
        self.configs = {}

    def get_config(self, cid):
        from src.bricks.system_settings.domain import CompanyConfig

        if cid not in self.configs:
            self.configs[cid] = CompanyConfig(company_id=cid)
        return self.configs[cid]

    def update_config(self, cfg):
        self.configs[cfg.company_id] = cfg
        return cfg


@pytest.fixture()
def svc():
    return SystemSettingsService(FakeRepo())


class TestTaxRates:
    def test_enum_values_match_spec(self):
        assert {(r.name, r.value) for r in TaxRate} == {
            ("VAT_0", 0),
            ("VAT_5", 5),
            ("VAT_8", 8),
            ("VAT_10", 10),
            ("NOT_TAXED", -1),
        }

    @pytest.mark.parametrize("rate", [0, 5, 8, 10])
    def test_validate_accepts_rates_in_force(self, svc, rate):
        """8% per NĐ 174/2025 (eff → 31/12/2026)."""
        svc.validate_vat_rate(rate)  # no raise

    def test_reduced_rate_bridge_fraction(self):
        from decimal import Decimal

        assert TaxRate.VAT_8.to_fraction() == Decimal("0.08")

    @pytest.mark.parametrize("bad", [-1, 2, 20, 100])
    def test_validate_rejects_others_EX(self, svc, bad):
        """NOT_TAXED(-1) is an item-level exemption flag, not a deductible rate."""
        with pytest.raises(InvalidRegimeError):
            svc.validate_vat_rate(bad)

    def test_default_config_has_law_rates(self, svc):
        cfg = svc.get_config(COMPANY)
        assert cfg.vat_rates == frozenset({0, 5, 10})

    def test_patch_vat_rates_is_law_locked(self, svc):
        svc.get_config(COMPANY)
        with pytest.raises(FlagLockedError):
            svc.set_vat_rates(COMPANY, {0, 5}, actor=ADMIN)


class TestEInvoiceSeries:
    def test_add_series_bumps_version_and_stores_ca(self, svc):
        s = svc.add_e_invoice_series(
            COMPANY,
            actor=ADMIN,
            prefix="HD/",
            ca_signer="VNPT-CA",
            approver=CHIEF,
        )
        assert s.active is True and s.next_sequence == 1
        cfg = svc.get_config(COMPANY)
        assert any(x.prefix == "HD/" for x in cfg.e_invoice_series)
        assert cfg.config_version == 1

    def test_sod_approver_must_differ(self, svc):
        with pytest.raises(SodViolationError):
            svc.add_e_invoice_series(
                COMPANY,
                actor=ADMIN,
                prefix="AB/",
                ca_signer=None,
                approver=ADMIN,
            )

    def test_max_15_series(self, svc):
        letters = [f"{chr(65+i//26)}{chr(65+i%26)}/" for i in range(15)]
        for pfx in letters:
            svc.add_e_invoice_series(
                COMPANY,
                actor=ADMIN,
                prefix=pfx,
                ca_signer="CA",
                approver=CHIEF,
            )
        with pytest.raises(MaxSeriesExceededError):
            svc.add_e_invoice_series(
                COMPANY,
                actor=ADMIN,
                prefix="ZZ/",
                ca_signer="CA",
                approver=CHIEF,
            )

    def test_duplicate_prefix_rejected(self, svc):
        svc.add_e_invoice_series(COMPANY, actor=ADMIN, prefix="HD/", ca_signer="CA", approver=CHIEF)
        with pytest.raises(DuplicateSeriesPrefixError):
            svc.add_e_invoice_series(
                COMPANY,
                actor=ADMIN,
                prefix="HD/",
                ca_signer="CA2",
                approver=CHIEF,
            )

    def test_percent_to_fraction_bridge(self):
        """Bridge to invoice/voucher decimal-fraction world."""
        from decimal import Decimal

        assert TaxRate.VAT_10.to_fraction() == Decimal("0.1")
        assert TaxRate.VAT_5.to_fraction() == Decimal("0.05")
        assert TaxRate.VAT_0.to_fraction() == Decimal(0)
