# Sign-Off: System Settings Module

## Review Sign-Off

| Role | Name | Date | Status | Comments |
|------|------|------|--------|----------|
| **Chief Accountant** | _Pending_ | _Pending_ | ☐ Reviewed | Legal compliance sign-off; VAT rate config; retention enforcement |
| **Product Owner** | _Pending_ | _Pending_ | ☐ Reviewed | Feature scope; P0 gap resolution timeline |
| **Lead Developer** | _Pending_ | _Pending_ | ☐ Reviewed | Domain layer complete; API + DB constraint gaps |
| **Big4 Auditor** | _Pending_ | _Pending_ | ☐ Reviewed | Audit trail adequacy; WORM enforcement; export capability |
| **Legal Consultant** | _Pending_ | _Pending_ | ☐ Reviewed | Vietnamese law compliance (LKT 2015, NĐ 123/2020, etc.) |

---

## Sign-Off Checklist

### P0 Critical — Must Resolve Before PROD Launch

- [ ] P0-03: Audit log WORM append-only + REVOKE DELETE constraint on `audit_log` table  
  legal basis: NĐ 13/2023 Art. 9; LKT 2015 Art. 30
- [ ] P0-04: MST validation enforced at API boundary + invoice/partner creation  
  legal basis: LKT 2015 Art. 28; QTV 71/2024 Art. 11
- [ ] P0-08: Soft-delete disabled on invoices/vouchers with ≥10y retention  
  legal basis: LKT 2015 Art. 30; NĐ 13/2023 Art. 9
- [ ] P0-09: Company tenant isolation + request-scoped context  
  legal basis: Luật Doanh nghiệp 2020
- [ ] P0-10: RBAC backend enforcement + MFA for privileged roles  
  legal basis: Big4 ITGC; SoD requirements
- [ ] P0-01: Full CompanyConfig API + all field validations  
  legal basis: LKT 2015 Art. 28
- [ ] P0-15: Backup + restore test procedure documented + quarterly tested  
  legal basis: auditor requirement; DR plan

### P1 Important — Fix Within 30 Days

- [ ] P1-01: Independent auditor data export (JSON + CSV)  
- [ ] P1-03: Concurrent edit detection (optimistic locking via config_version)  
- [ ] P1-04: E-invoice signing integration (SOFTWARE_CERT interim mode)  
- [ ] P1-05: CIT rate as system constant (currently 20%)

### P2 Nice-to-Have — Fix Within 90 Days

- [ ] P2-01: Multi-cost-center management  
- [ ] P2-02: COA versioning (TT200 ↔ TT99 switch-over)  
- [ ] P2-03: COA import/export (CSV seed script)  
- [ ] P2-05: Reconciliation exception management  
- [ ] P2-06: Password policy enforcement  
- [ ] P2-07: In-app notification for regulatory updates  

---

## Sign-Off Decision

**Current Verdict**: **CONDITIONAL — Domain layer + migration implemented; API + DB constraints pending**

**Launch Decision**: **NOT APPROVED for unrestricted PROD launch** — 6 P0 gaps remain

**Conditional Launch**: **MAY launch with restrictions** if:
- [ ] Chief Accountant signs off on remaining P0 gaps as "accepted risk"
- [ ] Auditors sign off on limited-functionality mode (read-only config, no write)
- [ ] Backup + restore procedure documented + tested
- [ ] All P1 gaps have mitigation plans (not necessarily resolved)

**Required Before Full PROD**: Resolve all P0-01 through P0-03, P0-08, P0-09, P0-10

**Sign-Off Workflow**:
1. Chief Accountant reviews all gaps + signs off (accepting risks or requesting resolution)
2. Lead Developer confirms implementation status for each gap
3. Big4 Auditor reviews audit trail design + export capability
4. Legal Consultant validates Vietnamese law compliance for implemented features
5. Product Owner confirms scope + timeline alignment
6. All sign-offs recorded above; "Full PROD" or "Conditional PROD" status updated

---

## Heritage

- **Created**: 2026-08-17  
- **Version**: 0.2.0  
- **Last reviewed**: _Pending_  
- **Review cycle**: Every 30 days or upon significant gap resolution  
- **Next review date**: _Pending_  

---