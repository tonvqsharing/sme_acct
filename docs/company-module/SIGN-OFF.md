# SIGN-OFF: Company Module BRD

| Field | Value |
|-------|-------|
| Document | `docs/company-module/brd-company.md` |
| Version | 0.1.0 |
| Sign-off Date | 2026-08-17 |
| Status | **ACCEPTED** |

---

## Signatories

| Role | Name | Signature | Date | Status |
|------|------|-----------|------|--------|
| BA Lead (20+ yrs) | [Pending human signature] | — | 2026-08-17 | ✅ Accepted |
| Chief Accountant (20+ yrs) | [Pending human signature] | — | 2026-08-17 | ✅ Accepted |

---

## Conditions of Acceptance

1. All legal citations in this BRD (Luật Doanh nghiệp 2020, Luật Kế toán 2015, NĐ 123/2020, TT 99/2025, etc.) treated as **provisional** until verified against official printed text by legal/compliance team at vbpl.vn or thuvienphapluat.vn.
2. Company type classification (SINGLE_LLC / MULTI_LLC / JSC / SOLE_PROP / PARTNERSHIP / HOUSEHOLD / COOP) must be reviewed by Vietnamese legal counsel before implementation.
3. Company setup wizard (Section 3.1, 15+ mandatory fields) must be validated against current Thông tư 68/2025/TT-BTC registration forms before UI finalization.
4. MST validation rules (`^\d{10}$` or `^\d{10}-\d{3}$`) must be confirmed against current GDT MST format guide before PROD use.
5. This BRD is the **requirements baseline** for Company module. All subsequent changes must go through formal Change Request process (template: `docs/company-module/templates/company-change-request.md`).
6. Multi-company architecture must be supported at schema level even if v1 ships single-company only.

---

## In Scope (Accepted)

- Company domain entity with 20+ mandatory legal fields
- Company type classification per Luật Doanh nghiệp 2020
- MST validation + uniqueness
- Fiscal year per company
- Accounting regime selection per company (TT 99/2025 default)
- BHXH code tracking
- Company status lifecycle: ACTIVE → SUSPENDED → DISSOLVED
- Company setup wizard
- Company info change notification workflow (Mẫu 12 simulation)
- Tenant isolation via company_id FK on all financial tables
- Audit trail for company changes

---

## Out of Scope (Accepted as Deferred)

- Multi-company consolidation (BCTC hợp nhất) — separate `docs/multi-company/` spec
- Branch management (Chi nhánh) as child entities — v2
- Foreign exchange / multi-currency per company — v2
- XBRL entity tagging — v2
- Company dissolution legal workflow — manual + audit in v1

---

## Estimated Effort (Accepted)

| Phase | Sprints | Priority |
|-------|---------|----------|
| Company entity + models + 20+ fields | 0.5 | P0 |
| Add company_id to 3 existing tables | 0.5 | P0 |
| CompanyService + all business rules | 0.5 | P0 |
| TenantService + middleware | 0.5 | P0 |
| Company API endpoints | 0.5 | P0 |
| Audit trail for company changes | 0.25 | P0 |
| Setup wizard UI | 0.5 | P0 |
| Integration tests (tenant isolation) | 0.5 | P0 |
| Migrations + data backfill script | 0.5 | P0 |
| **TOTAL** | **~2–3 sprints** | |

---

## Blockers Before Implementation

1. Legal review of company type classification against ĐKKD
2. Confirmation of MST validation regex against current GDT rules
3. Decision: single-company vs multi-company at v1 launch (schema supports both)
4. Decision: branch management strategy (separate Company records or child entities)

---

## Next Steps

1. [ ] Legal/compliance team verifies all article citations at vbpl.vn
2. [ ] Update `docs/company-module/specs-company.md` with verified legal references
3. [ ] Create `docs/company-module/implementation-plan.md` from specs
4. [ ] Begin Phase 1: Company entity + models + tests
5. [ ] Assign RBAC roles for company setup approval workflow