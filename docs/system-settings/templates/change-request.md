# Template: Config Change Request (CCR)

---

**CCR ID:** CCR-YYYY-NNN
**Date Submitted:** YYYY-MM-DD
**Requested By:** Name | Role
**Company:** Name | MST
**Reviewed By:** Name | Chief Accountant
**Approved By:** Name | Role
**Approved Date:** YYYY-MM-DD

---

## Change Summary

| Field | Value |
|-------|-------|
| Flag Name | `vat_settlement_cycle` |
| Current Value | `MONTHLY` |
| Proposed Value | `QUARTERLY` |
| Flag Type | CONFIG |
| Requires 2nd Approval | YES |
| Legal Basis | NĐ 123/2020/NĐ-CP Art. 24 (chu kỳ kê khai thuế) |

---

## Justification

[Explain why the change is needed. Link to business need, tax registration document, or management decision.]

---

## Impact Assessment

| Area | Impact | Risk |
|------|--------|------|
| Tax filing schedule | Quarterly instead of monthly; filings due Apr 30, Jul 31, Oct 31, Jan 31 | Medium: missing deadline = penalty |
| Accounting period definition | Must align with quarters | Low: derived automatically |
| Cash flow forecasting | Less frequent outflows | Positive |
| Staff workload | lower frequency, higher per-event effort | Medium |

---

## Regulatory Check

- [ ] Change permitted under current tax registration (MST declared quarterly if revenue ≤ VND 1B/year)
- [ ] No open tax audit on affected periods
- [ ] FY is not closed for change (1 re-opened month)
- [ ] Prior VAT filings use old cycle; re-submission not required

---

## Implementation Steps

1. [ ] Change config_version +1 in company_configs
2. [ ] Record before/after in config_changes
3. [ ] Emit AUDIT events
4. [ ] Notify CA + A
5. [ ] Re-test VAT export logic for quarterly periods

---

## Rollback Plan

If error:
- Revert PATCH /config/flags/vat_settlement_cycle to previous value
- Recompute FY periods; alert CA

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Requester | | | YYYY-MM-DD |
| Chief Accountant | | | YYYY-MM-DD |
| Admin | | | YYYY-MM-DD |