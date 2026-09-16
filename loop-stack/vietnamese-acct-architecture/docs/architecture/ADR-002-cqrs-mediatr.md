# ADR-002: CQRS with MediatR

## Status

Accepted

## Date

2026-09-16

## Context

Need clear separation of commands and queries for accounting operations:
- Commands: CreateAccount, PostJournalEntry, ClosePeriod (write-heavy, require validation)
- Queries: GetBalanceSheet, GetIncomeStatement, GetAccounts (read-heavy, optimized for reporting)

Forces at play:
- Financial reporting (B01-DN, B02-DN, B03-DN) requires optimized read models
- Journal entry posting requires complex validation (debit=credit, period open)
- Multiple handlers per command/query possible (cross-cutting concerns)
- Need for pipeline behaviors (validation, logging, audit trail)

## Decision

Use CQRS with MediatR:

- **Commands**: Represent state-changing operations; return results (not void)
- **Queries**: Represent data retrieval; return DTOs
- **Handlers**: One handler per command/query; contain business logic
- **Validators**: FluentValidation validators for command/query validation
- **Pipeline Behaviors**: Cross-cutting concerns (validation, logging, audit)

MediatR 14.2.0 provides:
- `IRequest<T>` for commands/queries
- `IRequestHandler<TRequest, TResponse>` for handlers
- `IPipelineBehavior<TRequest, TResponse>` for cross-cutting concerns
- DI integration via `AddMediatR(cfg => cfg.RegisterServicesFromAssembly(...))`

## Consequences

### Positive
- Clear responsibility: each handler does one thing
- Read/write models can evolve independently
- Validation pipeline ensures consistent error handling
- Easy to add cross-cutting concerns (logging, audit, performance)
- Handlers are independently testable

### Negative
- More files (one handler per command/query)
- indirection layer between controllers and business logic
- Need to manage MediatR pipeline ordering
- DTOs required for data transfer between layers

## Notes

- Domain events (plain records) are separate from MediatR events
- Domain events raised by entities, dispatched by Infrastructure/Application layer
- MediatR only used in Application layer, not in Domain
- See `docs/architecture/ADR-003-posting-seam.md` for posting seam design
