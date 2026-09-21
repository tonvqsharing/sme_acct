# System / Security Default Seed Data

## Purpose
Provide company-scoped default masters for VoucherType, TransactionReason and DocumentNumberingSeries to be seeded per new Company creation.

## VoucherType defaults
Per company, create VoucherTypes with unique Code per company.

| Code | Name | VoucherCategory |
|------|------|-----------------|
| RCPT | Receipt | Receipt |
| PMT  | Payment | Payment |
| JNRL | Journal | Journal |
| ADJ  | Adjustment | Adjustment |
| OPEN | Opening | Opening |

## TransactionReason defaults
Per VoucherType, create reasons with unique Code per company.

RCPT:
- CASH, Cash Receipt
- BANK, Bank Transfer Receipt
- SALES, Sales Receipt

PMT:
- CASH, Cash Payment
- BANK, Bank Transfer Payment
- PURCH, Purchase Payment

JNRL:
- ADJ, General Adjustment
- REVAL, Revaluation
- CLOS, Closing Entry

ADJ:
- CORR, Correction
- REV, Reversal

OPEN:
- OPEN, Opening Balance

## DocumentNumberingSeries defaults
Per VoucherType, create default series with Prefix = VoucherType Code.

| VoucherTypeCode | Prefix | Start | Padding |
|-----------------|--------|-------|---------|
| RCPT | RCPT- | 1 | 6 |
| PMT  | PMT-  | 1 | 6 |
| JNRL | JNRL- | 1 | 6 |
| ADJ  | ADJ-  | 1 | 6 |
| OPEN | OPEN- | 1 | 6 |

## Implementation notes
- Seed inside Application service `CreateCompanyWithDefaultsCommandHandler` using Domain factories.
- Ensure `CompanyId` FK Restrict, unique indexes per company enforced.
- Use `IUnitOfWork.SaveChangesAsync` within one transaction.
- DocumentNumberingSeries.Increment must be called within same EF transaction to leverage xmin optimistic concurrency.
- Do not seed Users/Roles; Users are global with ExternalId from Microsoft Entra.
