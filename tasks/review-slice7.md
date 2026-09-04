# Review Slice 7 — Sales GDT real-sign seam (no 3P)

## Context
- `issue_einvoice` was a mock inline in `web_adapter` (mutated domain, touched `_repo`/`_audit` privates, no XML payload). Builds real GDT-tagged XML + signer port while staying mock-default: no CA, no network this version.

## Correctness
- [x] `build_einvoice_xml` emits `DLHDon/HDon` vocabulary (`KHMSHDon/KMHHDON/SHDon/NLap/NBan/NMua/HHDVu/THTTLTE/TTCKTM/TongCong/DVTTe`) matching `xml_ingest` parse paths; round-trip test asserts number/template/buyer-MST survive GDT parse
- [x] Escaping via `xml.sax.saxutils` (same as `export_gdt_xml`); malformed-content test proves well-formedness with `<A> &`
- [x] Guards: DRAFT → `NotPostedError` 422, double issue → `AlreadyIssuedError` 409, missing ký hiệu → 422, empty items → 422
- [x] Service `issue_einvoice` reproduces prior mock outcomes (SENT + checksum + audit) so existing `test_issue_mock`/`test_issue_requires_posted` stay green with one payload fix (ký hiệu now required — the point of the slice)
- [x] Tests: 8 new RED→GREEN + 1 existing payload fix; full suite 1045 passed (1037 + 8)

## Readability
- [x] `einvoice.py` 100 lines pure; service method 30 lines; web handler shrank (deleted 30-line inline block); new exceptions sit beside `AlreadyPostedError`

## Architecture
- [x] Boundary fix: web no longer touches `_repo`/`_audit` privates — delegates to service port
- [x] Signer injected (`signer.sign(xml, actor)`), default `mock_sign` sha256; sender deliberately absent (SENT = signed mock, same as before) — real CA/sender plug in next version without signature change
- [x] Tag strings duplicated from `xml_ingest` (8 tags) instead of cross-brick import — brick-boundary law wins over DRY here; noted
- [x] Audit now carries `xml_hash` + `signature` for GDT traceability

## Security
- [x] SOD unchanged (CHIEF/ADMIN only); MST validated at create-time already; XML escaped (no injection into GDT payload); no secrets; no network calls

## Performance
- [x] One extra XML render per issue (small, non-hot path); no list-endpoint change

## Verification
- [x] `ruff check src tests` pass
- [x] `black --check src tests` pass
- [x] `mypy --ignore-missing-imports src/bricks/` pass (129 files)
- [x] `pytest -q` 1045 passed

## Verdict
- [x] **Approve** — merge Slice 7.
