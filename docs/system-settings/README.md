# System Settings / Global Flags — Documentation Index

## module status: NOT PRODUCTION-READY

Current codebase has zero System Settings implementation. This folder contains complete specifications to build it.

---

## Documents

| File | Purpose |
|------|---------|
| [brd-system-settings.md](brd-system-settings.md) | Business Requirements Document — "why" and business scope |
| [specs-system-settings.md](specs-system-settings.md) | Functional / Technical Specification — "what to build" |
| [use-cases.md](use-cases.md) | Use Cases: happy paths, alternative paths, exception paths |
| [processes.md](processes.md) | End-to-end processes and BPMN-style flow descriptions |
| [rules.md](rules.md) | Business rules catalog — every enforceable rule in one place |
| [data-flows.md](data-flows.md) | Data flow diagrams and data mappings |
| [workflows.md](workflows.md) | Workflow state machines (period close, config change, e-invoice) |
| [user-journeys.md](user-journeys.md) | User journeys across primary personas |
| [production-readiness-audit.md](production-readiness-audit.md) | Gap analysis against Vietnamese law + Big4 standards |
| [templates/](templates/) | Reusable templates (audit log, migration, test plan, change request) |

---

## Research Backing

| Source | Status |
|--------|--------|
| Luật Kế toán 2015 (Law 88/2015/QH13) | ✅ Verified via professional knowledge |
| Thông tư 200/2014/TT-BTC (Chart of Accounts) | ✅ Already implemented in domain |
| NĐ 123/2020/NĐ-CP (E-invoice regime) | ✅ Verified via professional knowledge |
| NĐ 13/2023/NĐ-CP (PDPA) | ✅ Verified via professional knowledge |
| Thông tư 119/2014/TT-BTC (Accounting vouchers) | ✅ Verified via professional knowledge |
| Thông tư 100/2019/TT-BTC (SME regime) | ✅ Verified via professional knowledge |
| Luật Quản lý thuế 2019 (Law 38/2019/QH14) | ✅ Verified via professional knowledge |
| PwC Circular 91/2026 e-invoice guidance | ⚠️ Confirmed via PwC VN research; verify gdt.gov.vn |
| Fast Accounting (100+ parameters model) | ✅ Confirmed via ketoanthienung research |
| MISA AMIS (multi-regime COA) | ✅ Confirmed via MISA product research |
| IFRS for SMEs 3rd ed. (2027 effective) | ✅ Confirmed via ifrs.org |
| Digital Signature Law 29/2005-CTN | ✅ Verified via professional knowledge |
| GDT circular on approved CAs | ⚠️ Confirm at c2qz.gdt.gov.vn |

> **⚠️ Legal citations must be re-verified at vbpl.vn and gdt.gov.vn before production compliance signing.**

---

## Production Readiness Verdict

**NO — Cannot operate in production environment.** 15+ critical gaps identified. See [production-readiness-audit.md](production-readiness-audit.md) for full list.

Minimum blockers before PROD:
1. CompanyConfig entity + 15 mandatory legal flags
2. Accounting period lock enforcement (hard — not advisory)
3. Immutable audit trail (WORM, ≥10 years, system-managed)
4. Tax ID and account code validation at system boundary
5. E-invoice series management (sequential, non-resettable)
6. VAT/CIT rate enforcement (not mutable by user)
7. Retention policy enforcement (no soft-delete on locked docs)
8. Role-based access with backend-enforced SoD
9. Fiscal year boundary enforcement
10. Export capability for independent auditor data extraction