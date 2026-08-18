# Production-Readiness Audit — Currencies & Exchange Rates Module

| | |
|---|---|
| Module | Currencies & Exchange Rates |
| Audit date | 2026-08-18 |
| Auditors | BA Lead + Chief Accountant (research phase) |
| Verdict | 🔴 **NOT PROD-READY — module does not exist** |

## 1. Executive verdict

**The application CANNOT operate a Currencies & Exchange Rates module in PROD ENV.**

No currency, exchange-rate, or revaluation capability exists in the codebase.
This is a greenfield build, not a gap-fix. All items below are key points that
must be implemented before any PROD operation.

## 2. Evidence — current state (verified by codegraph, 2026-08-18)

| Check | Result |
|---|---|
| Currency entity in `src/domain/entities/` | ❌ ABSENT (only base/company_config/company/contact/invoice/user/voucher) |
| ExchangeRate entity | ❌ ABSENT |
| FX service (`application/services/`) | ❌ ABSENT |
| Currency tables in `src/infrastructure/database/models.py` | ❌ ABSENT |
| Currency column on Invoice/Voucher/BankAccount | ❌ ABSENT (all amounts implicitly VND) |
| FX flags in CompanyConfig | ❌ ABSENT |
| FX API routes | ❌ ABSENT |
| FX RBAC decorators | ❌ ABSENT |
| FX tests | ❌ ABSENT |
| Money handling | ⚠️ Decimal amounts only, no currency context |

## 3. Key points for PROD (what must exist)

### 3.1 Legal compliance (non-negotiable)

1. **TT 99/2025/TT-BTC** (effective 01/01/2026, replaces TT 200/2014) — revaluation
   at tỷ giá mua bán chuyển khoản trung bình of NHTM nơi DN thường xuyên giao dịch;
   demand deposits at bank of account; consistency principle.
2. **ND 254/2026/NĐ-CP** (effective 01/07/2026, replaces ND 123/2020) — e-invoice FX
   rules; invoice must state tỷ giá quy đổi ra VND; FX use limited to permitted cases.
3. **VAS 10** — monetary items at closing rate, non-monetary at historical.
4. **TK 515/635 direct posting** default; TK 413 per Điều 60 TT 99/2025 configurable.
5. **Pháp lệnh ngoại hối 2005/2013 + ND 70/2014/NĐ-CP + TT 32/2013/TT-NHNN** —
   FX use restrictions; ND 340/2025/NĐ-CP sanctions.
6. **Booking-rate rule** — Nợ at actual transaction rate, Có at bình quân gia quyền
   or actual (TT 99/2025; TT 133/2016 Điều 52-53).

### 3.2 Functional (minimum viable for PROD)

1. Currency master data (ISO 4217) with VND base immutable.
2. Exchange-rate storage per (currency, date, type) with history (no in-place edit).
3. CSV batch import + manual entry + audit trail; NHNN sync (v1.5).
4. Dual-currency booking: original + VND + frozen rate on every FX transaction.
5. Period-end revaluation: DRAFT → APPROVE → POST; idempotent re-run; balanced postings.
6. FX difference report + rate history report.
7. Period-lock integration; approval chain (CHIEF_ACCOUNTANT 2nd approval).
8. Audit log on every mutation; RBAC `@casbin_required` on all routes; AUDITOR read-only.

### 3.3 Architecture (per AGENTS.md / CODING_CONVENTION)

1. Domain layer pure Python — no sqlalchemy/Flask imports.
2. Enums duplicated domain + SQLAlchemy (sync both).
3. Repository ports in `application/ports/`.
4. TDD per TESTING_STRATEGY.md (unit + integration; no UI-level for pure logic).
5. Migration via flask-migrate; supported DB URIs.

## 4. Gap analysis (current → PROD)

| # | Capability | Current | Needed | Effort |
|---|---|---|---|---|
| 1 | Currency master | none | entity + model + API + tests | M |
| 2 | Exchange rates | none | entity + model + API + import | M |
| 3 | Booking rate resolution | none | service (actual + weighted avg) | M |
| 4 | Dual-currency amounts | none | schema change on invoice/voucher/bank | M |
| 5 | Revaluation engine | none | service + journal postings + approval | L |
| 6 | FX reporting | none | report queries + serializers | M |
| 7 | Config flags | none | CompanyConfig extension + migration | S |
| 8 | NHNN sync | none | fetcher (v1.5) | S-M |
| 9 | RBAC + audit | existing infra | decorators + audit wiring | S |
| 10 | Tests | none | unit + integration | M-L |

Effort: S < 2d, M 2–5d, L 1–2w (per engineer, rough).

## 5. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Wrong booking rate → misstated FS/tax | HIGH | Hard-code R1 rules; weighted avg computed, not typed |
| Revaluation imbalance | HIGH | D6 balance tol 0.01, atomic transaction |
| Rate changes after post → audit failure | HIGH | D3 immutability; new row supersedes |
| Revaluation in locked period | HIGH | D8 period-lock guard |
| Non-compliance ND 254/2026 e-invoice FX | HIGH | R5 capture tỷ giá quy đổi; field mandatory on FX invoices |
| Unauthorized revaluation posting | MED | D9 approval chain + RBAC |
| NHNN source unavailable (v1.5) | MED | manual fallback (Tryton/Odoo lesson) |
| Multi-company consolidation | MED | blocked per AGENTS.md until tenant isolation; out of scope v1 |

## 6. Compliance checklist (per TESTING_STRATEGY.md + AGENTS.md)

- [ ] No SQLAlchemy/Flask imports in `src/domain/`.
- [ ] Enums synced domain + models.
- [ ] `@casbin_required` on all FX API routes; AUDITOR read-only backend-enforced.
- [ ] Tests: unit (domain rules) + integration (repo/API); no UI-level for pure logic.
- [ ] pytest green; ruff/black/mypy pass before merge.
- [ ] Migration applied + tested on sqlite/mysql/postgres.
- [ ] Audit log wired for: rate create/import, revaluation runs, config changes.
- [ ] Laws double-checked at implementation time (docs cited above are primary-source verified 2026-08-18).

## 7. Recommendation

1. Approve this doc set as spec baseline.
2. Implement in order: (a) domain entities + rules + unit tests → (b) models + migration
   → (c) repository adapters → (d) services → (e) API + RBAC → (f) import/reporting
   → (g) v1.5 NHNN sync.
3. Re-run this audit after each milestone; sign off at POSTED-capable milestone.

## 8. Sign-off gates

| Gate | Criteria |
|---|---|
| G1 Spec approved | BRD/specs/UC signed (SIGN-OFF.md) |
| G2 Domain green | unit tests for R1-R8, D1-D11 pass |
| G3 Integration green | repo + API integration tests pass |
| G4 Compliance green | ruff + black + mypy + pytest pass |
| G5 PROD-ready | full checklist §6 green + period-end revaluation E2E on real regime (TT 99/2025) |

**Until G5, module is NOT PROD-ready.**