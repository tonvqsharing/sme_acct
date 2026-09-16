# Circular 99/2025/TT-BTC — Architecture Mapping

## Overview

Circular 99/2025/TT-BTC issued October 27, 2025, effective January 1, 2026. Replaces Circular 200/2014/TT-BTC. Defines enterprise accounting regime including software requirements.

## Article 28 — Software Requirements → Architecture Layers

| Art. 28 | Requirement | Architecture Layer | Enforcement Point | Implementation |
|---------|-------------|-------------------|-------------------|----------------|
| **(a)** | Procedures/operations must comply with accounting laws, tax laws — must not alter nature/principles/methods of accounting | **Domain** | Posting rules, validation | `PostingService` enforces debit=credit, period-open rules; `Account` entity enforces COA structure |
| **(c)** | Data must be secure; system must alert or prevent intentional interference that alters recorded information | **Domain + Infrastructure** | Immutability, audit trail | `JournalEntry.IsPosted` flag; `IAuditLogger` append-only; EF Core concurrency (`xmin`) |
| **(d)** | Must provide complete and timely output information as required by authorities | **Application** | Report generation | `IAccountingReportService` generates B01-DN, B02-DN, B03-DN; query handlers for balance sheet/income statement |
| **(dd)** | Must be capable of connecting or ready to connect with other software (e-invoice, digital signature, etc.) | **Infrastructure** | Port/adapter interfaces | `IEInvoiceProvider`, `IDigitalSignatureService` port interfaces; adapter stubs for TVAN providers |
| **(e)** | Must be capable of being upgraded/modified to comply with changes in laws | **All layers** | Extensibility design | Modular architecture; COA extensibility (add/modify accounts); `Account` entity supports lifecycle (add/deprecate) |

## Chart of Accounts Requirements

- Accounts eliminated: 161, 441, 611, 631
- New accounts: 215 (Biological Assets), 332 (Dividends Payable), 82112 (GMT Top-Up Tax)
- Renamed accounts: 112 now "Demand deposits"
- Enterprises may supplement accounts or amend names/codes/contents per Art. 25
- Must issue internal accounting policy documenting any changes

## Posting Rules

- Journal entries must balance: Σ(debit) == Σ(credit)
- Posted entries cannot be modified, only reversed
- Every entry must trace to source document (source_type + source_id)
- Corrections must maintain chronological order with traces preserved

## Fiscal Period Requirements

- Fiscal year is global (single company)
- Periods have Open/Closing/Closed lifecycle
- Closed periods cannot accept new postings
- Transitional provisions for Circular 200 → 99 migration

## E-Invoice Integration

- Mandatory since July 1, 2022 (Decree 123/2020)
- Two types: with code (real-time GDT clearance) and without code
- XML is legally binding format (not PDF)
- Digital signature mandatory
- TVAN provider integration required

See [EInvoice-integration.md](./EInvoice-integration.md) for port interface design.

## Digital Signature Requirements

- GDT-approved certificate (USB token or cloud HSM)
- Required for all e-invoices except POS cash registers
- Separate port interface: `IDigitalSignatureService`

## Full Article Structure

| Chapter | Article | Title | Architecture Impact |
|---------|---------|-------|---------------------|
| I — General | Art. 1 | Scope of regulation | Defines what software must cover |
| | Art. 2 | Subjects of application | Single-company scope confirmed |
| | Art. 3 | Corporate governance and internal control | Audit trail, access control design |
| | Art. 4 | Accounting currency | `Currency` value object, exchange rate handling |
| | Art. 5-7 | Accounting principles | Domain service validation rules |
| II — Documents | Art. 8 | General provisions | Document entity design |
| | Art. 9 | Standard forms | Flexible voucher template system |
| | Art. 10 | Preparation and signing | Authorization controls |
| III — Accounts | Art. 11 | Chart of accounts | `Account` entity extensibility; COA seed data |
| | Art. 22 | Account application | Default COA loading |
| | Art. 25 | Account modification | Account lifecycle management |
| | Art. 26 | Unaddressed transactions | Fallback handling |
| IV — Books | Art. 12 | Accounting books | Journal entry entity design |
| | Art. 27-28 | Book templates | Flexible book template system |
| V — Financial Statements | Art. 29 | General provisions | Report generation handlers |
| | Art. 30 | Statement of Financial Position | B01-DN report model |
| | Art. 31-35 | Other statements | B02-DN, B03-DN report models |
| | Art. 36 | Transitional provisions | Migration/transitional handling |
| VI — Implementation | Art. 28* | Use of accounting software | Architecture enforcement points |
| | Art. 37-38 | Implementation | User role design |

## Traceability Matrix

| Regulation | Article/Section | Architecture Component | Layer | Test | Status |
|-----------|-----------------|----------------------|-------|------|--------|
| Circular 99 | Art. 28(a) | PostingService | Domain | PostingRuleTests | Planned |
| Circular 99 | Art. 28(c) | JournalEntry.IsPosted | Domain | PostingRuleTests | Planned |
| Circular 99 | Art. 28(c) | IAuditLogger | Infrastructure | AuditTests | Planned |
| Circular 99 | Art. 28(d) | IAccountingReportService | Application | ReportingTests | Planned |
| Circular 99 | Art. 28(dd) | IEInvoiceProvider | Infrastructure | EInvoiceAdapterTests | Planned |
| Circular 99 | Art. 28(e) | Account lifecycle | Domain | AccountLifecycleTests | Planned |
| Circular 99 | Art. 11 | Account entity | Domain | AccountTests | Planned |
| Circular 99 | Art. 25 | Account modification | Domain | AccountLifecycleTests | Planned |

## Example Traceability Chain

```
Circular 99 Art. 28(c) — "prevent intentional interference"
  → Domain: JournalEntry.IsPosted = true after posting
  → Domain: JournalEntry cannot be modified after IsPosted
  → Infrastructure: IAuditLogger.Append() — append-only log
  → Test: PostingRuleTests.PostedEntryCannotBeModified()
  → Test: AuditTests.AuditLogIsAppendOnly()
```
