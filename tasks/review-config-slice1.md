# Review Config Slice 1 — Law thresholds as CONFIG flags

## Context
- Moves `NON_CASH_THRESHOLD` (5tr, NĐ181) and `MAX_SERIES` (15) from code consts to `CompanyConfig` flags, so gov changes need panel update — not deploy. Series-cap check now reads `cfg.max_einvoice_series`.

## Correctness
- [x] Flags versioned via `with_flag_update` (+1), validators reject bad (`-5`, `0`, `bool` guard since `bool` is `int` subclass)
- [x] Storage round-trip (columns + `_to_domain` + `update_config`); API serializes both flags
- [x] Series cap enforced from config (same 409 code); purchases threshold wiring explicitly deferred to Slice 2 — const still default there
- [x] Tests: 4 unit RED→GREEN + 1 integration (panel update, version bump, bad-value 422); full suite 1050 passed (1045 + 5)

## Readability
- [x] Validators mirror sibling branches; one `noqa: SIM102` with reason (ruff false-positive shape shared by existing branches)

## Architecture
- [x] Follows `CONFIG_FLAGS` allowlist law; no new ports; no cross-brick change; math/protocol consts untouched (tolerance, checksum, pagination)

## Security
- [x] Flag PATCH keeps existing role gate + optimistic `config_version` conflict; AUDITOR path unchanged; no secrets

## Performance
- [x] No new queries (config already loaded per call)

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (129 files)
- [x] `pytest -q` 1050 passed

## Verdict
- [x] **Approve** — merge Config Slice 1.
