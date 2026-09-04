"""TDD RED — Slice 1: law thresholds as CONFIG flags."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.system_settings.domain import CompanyConfig

COMPANY = uuid4()


def _cfg():
    return CompanyConfig(company_id=COMPANY)


def test_non_cash_threshold_update_versions():
    cfg = _cfg()
    out = cfg.with_flag_update("non_cash_threshold", 10000000, uuid4())
    assert out.config_version == cfg.config_version + 1


def test_non_cash_threshold_rejects_bad():
    with pytest.raises(ValueError, match="non_cash_threshold"):
        _cfg().with_flag_update("non_cash_threshold", -5, uuid4())


def test_max_einvoice_series_update_versions():
    cfg = _cfg()
    out = cfg.with_flag_update("max_einvoice_series", 10, uuid4())
    assert out.config_version == cfg.config_version + 1


def test_max_einvoice_series_rejects_bad():
    with pytest.raises(ValueError, match="max_einvoice_series"):
        _cfg().with_flag_update("max_einvoice_series", 0, uuid4())
