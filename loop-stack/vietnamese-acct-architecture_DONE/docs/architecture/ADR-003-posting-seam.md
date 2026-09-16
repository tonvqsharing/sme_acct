# ADR-003: Accounting Posting Seam

## Status

Accepted

## Date

2026-09-16

## Context

Critical architectural question: where does accounting posting happen? Business modules (Sales, Purchasing, Inventory) need to generate journal entries, but posting rules (debit=credit, period open, account validation) must be domain-driven and independently testable.

Forces at play:
- Sales module knows nothing about debit/credit rules
- Posting rules must be independently testable without HTTP/database
- Regulatory traceability: every posting must link to source event
- Circular 99 Art. 28(c): "prevent intentional interference" requires immutability after posting

## Decision

Accounting posting is a **domain service** within Accounting Core:

```
Business Module (e.g., Sales)          Accounting Core
──────────────────────────             ─────────────────
SalesInvoiceCreated                   IPostingService.Post(entry)
  → Domain Event                        → validates balance
  → Handler invokes IPostingService     → enforces rules
                                        → persists via IJournalEntryRepository
                                        → raises JournalEntryPosted event
```

### Posting Flow

1. Business module creates transaction (e.g., SalesInvoice)
2. Business module raises domain event (e.g., SalesInvoiceCreated)
3. Application handler receives event
4. Handler constructs JournalEntry from event data
5. Handler invokes `IPostingService.Post(entry)`
6. PostingService validates:
   - Period is open
   - All accounts are leaf nodes
   - Debit equals credit
7. PostingService persists via `IJournalEntryRepository`
8. PostingService raises `JournalEntryPosted` domain event
9. Audit trail recorded via `IAuditLogger`

### Port Interface

```csharp
namespace SmeAccounting.Domain.Ports;

public interface IPostingService
{
    Task<JournalEntry> PostAsync(JournalEntry entry, CancellationToken cancellationToken = default);
}
```

## Consequences

### Positive
- Sales module knows nothing about debit/credit rules
- Posting rules are independently testable
- Regulatory traceability: every posting links to source event
- Domain events decouple business modules from accounting core
- Immutable after posting (Circular 99 Art. 28(c) compliance)

### Negative
- Orchestration complexity: multiple domain events and handlers
- Need for correlation IDs to trace posting back to source
- Potential performance overhead from event dispatching
- Debugging requires understanding event flow

## Notes

- PostingService is a domain service interface in Domain layer
- Implementation lives in Application layer (orchestration) or Infrastructure (persistence)
- Domain events (plain records) are raised by entities, dispatched by Infrastructure/Application
- See `docs/regulatory/Circular99-mapping.md` for regulatory compliance mapping
- See `docs/regulatory/ChartOfAccounts-structure.md` for account validation rules
