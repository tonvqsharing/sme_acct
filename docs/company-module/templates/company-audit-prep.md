# Template: Company Audit Preparation

Pre-audit readiness for Company master data — Vietnamese General Tax Department + independent statutory auditor.

---

## Pre-Audit Checklist

### 30 Days Before
- [ ] All company records have `legal_reviewed_at` stamped
- [ ] No `MST_CHANGED` events in last 90 days without GDT notification proof on file
- [ ] Company type matches ĐKKD exactly
- [ ] Fiscal year start matches company charter
- [ ] Responsible accountant MSKHMN valid and current

### 7 Days Before
- [ ] Run: `GET /api/v1/companies/{id}/audit-log?from={fyear_start}&to={fyear_end}`
- [ ] Verify: all changes in period are in audit_log
- [ ] Verify: no unauthorized MST changes
- [ ] Verify: no FLAG_VIOLATION events on company type or legal name fields
- [ ] Verify: bank accounts match bank statements

### Day of Audit
- [ ] Present: Company entity JSON (current state)
- [ ] Present: ĐKKD scan vs system legal_name (exact match)
- [ ] Present: MST card vs system MST
- [ ] Provide: full audit_log for company changes
- [ ] Provide: partner/voucher/invoice sample showing company_id linkage
- [ ] Provide: proof of legal_review stamp (digital signature or CA signature)

---

## Evidence Package

| Item | Format | Source |
|------|--------|---------|
| Company legal info snapshot | JSON (GET /companies/{id}) | System API |
| ĐKKD scan | PDF (original + scan) | External / Admin |
| MST registration card | PDF | External / Admin |
| Company change history | CSV (from /companies/{id}/audit-log) | System API |
| Config changes log | CSV (from /companies/{id}/audit-log) | System API |
| Responsible accountant license | PDF copy | External |
| BHXH registration confirmation | PDF | External / System (future API) |
| Bank account confirmation | PDF from bank | External |