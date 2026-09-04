# Review Slice 1 — Party base (Customer/Supplier/Employee + Department)

## Context
- Implements missing must-have masters: Party base with role flags + Department, MST validate, duplicate 409, company isolation, RBAC, audit, checksum.

## Correctness
- [x] Matches spec: Party code unique/company, MST 10/13 valid (010...), duplicate code/MST 409, at least one role, company isolation
- [x] Edge: invalid MST 000... 422, empty role ValueError, missing actor/reason ValueError
- [x] Error paths: duplicate 409, invalid 422, AUDITOR 403, isolation OK
- [x] Tests: 7 unit (create, MST, duplicate code/MST, isolation, role filter, role required) + 4 integration (create+list, duplicate, auditor, invalid, department) — all green

## Readability
- [x] Names clear: Party/Department, is_customer/supplier/employee, _valid_mst
- [x] Logic straightforward, no clever tricks, 126 lines service

## Architecture
- [x] Lego 5-file: domain pure, contract ports, storage 2 tables Base, service ports Any, web @login_required only Flask file
- [x] No cross-brick joins, primitives only, company_id FK
- [x] Wiring: PartyBase.create_all, party_bp, SQLAlchemyPartyRepository, PartyService audit, app.party_service, alembic PartyBase

## Security
- [x] MST validate at boundary, code strip, actor+reason, company isolation, AUDITOR 403, no secrets, SQLA param

## Performance
- [x] No N+1, list by company_id indexed, role filter DB-side, no unbounded, pagination not needed (SME <1k parties)

## Verification
- [x] `ruff check` 0
- [x] `black --check` 0
- [x] `mypy --ignore-missing-imports src/bricks/party` 0
- [x] `pytest tests/unit/party tests/integration/test_party_api.py -q` 11 passed
- [x] `pytest tests -q` 1011 passed

## Verdict
- [x] **Approve** — Ready to merge slice 1. Done only when pass, now pass.
