# Template: Company Info Change Request (CCR)

---

**CCR ID:** CCR-COMPANY-YYYY-NNN
**Date Submitted:** YYYY-MM-DD
**Requested By:** Name | Role
**Company:** Name | MST
**Reviewed By:** Name | Chief Accountant
**Approved By:** Name | Role
**Approved Date:** YYYY-MM-DD

---

## Change Summary

| Field | Current Value | Proposed Value | Restricted? |
|-------|--------------|---------------|-------------|
| legal_name | "Công ty ABC" | "Công ty ABC Việt Nam" | YES |
| MST | 0123456789 | 9876543210 | YES |
| address | "123 Đường A" | "456 Đường B" | YES |
| phone | "0281111111" | "0282222222" | NO |
| bank_account | "VCB 123" | "VCB 456" | NO |

---

## Justification

[Explain why the change is needed. For RESTRICTED fields: attach Mẫu 12 / Mẫu 47 scan.]

---

## Regulatory Check

- [ ] Mẫu 12 / Mẫu 47 filed with DPI / Tax authority (for RESTRICTED fields)
- [ ] New ĐKKD / MST received from authority
- [ ] Effective date defined
- [ ] Downstream notifications planned (bank, customers, e-invoice provider)

---

## Implementation Steps

1. [ ] Verify GDT / DPI documentation
2. [ ] Update company record via API / UI
3. [ ] Update all future-dated documents
4. [ ] Notify customers/suppliers of name/MST change
5. [ ] Update e-invoice registration with CA if MST changed
6. [ ] Record change in audit_log + config_changes

---

## Rollback Plan

If error:
- Revert PATCH if effective_date is future
- If effective_date passed: issue correction note
- Notify tax authority of reversal

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Requester | | | YYYY-MM-DD |
| Chief Accountant | | | YYYY-MM-DD |
| Admin | | | YYYY-MM-DD |
| Legal (if restricted) | | | YYYY-MM-DD |