# ADR-001: Clean Architecture

## Status

Accepted

## Date

2026-09-16

## Context

Vietnamese accounting application needs regulatory compliance (Circular 99, VAS, Decree 123) and testability. Prior project had dependency chaos with layers referencing each other arbitrarily. Need strict dependency direction to enable:
- Independent testing of accounting rules without HTTP/database
- Regulatory compliance enforcement via architecture tests
- Clear separation of concerns for audit trail

Forces at play:
- Circular 99 Art. 28(c): "prevent intentional interference" requires immutability and audit trail
- Single-company SME scope eliminates multi-tenant complexity
- Need for e-invoice integration (TVAN providers) via port/adapter pattern
- Domain events for accounting posting must be domain-driven

## Decision

Use Clean Architecture with dependency inversion:

```
Presentation (Api) → Application → Domain ← Infrastructure → Application
```

- **Domain layer**: Pure .NET class library, zero NuGet refs, contains entities, value objects, domain events, port interfaces
- **Application layer**: Business logic, CQRS handlers, validators, DTOs; depends only on Domain
- **Infrastructure layer**: EF Core, external service adapters; implements Domain/Application ports
- **Api layer**: ASP.NET MVC controllers (thin: HTTP → MediatR dispatch); depends only on Application

Dependencies flow toward the innermost circle (Domain). All outer layers depend on inner layers, never the reverse.

## Consequences

### Positive
- Domain logic independently testable (no HTTP/DB dependency)
- Regulatory compliance enforced via architecture tests (NetArchTest.Rules)
- Port/adapter pattern enables swapping TVAN providers without domain changes
- Domain events decouple business modules from accounting posting rules
- Audit trail and immutability cleanly separated in Infrastructure

### Negative
- More files and projects (4 projects + test project)
- Steeper learning curve for developers unfamiliar with DDD/Clean Architecture
- Need architecture tests to enforce dependency rules
- Port interfaces add indirection layer

## Notes

- Follows Michael Nygard ADR format
- References: Microsoft eShopOnWeb, Jason Taylor CleanArchitecture template
- Enforced by `SmeAccounting.ArchitectureTests` project using NetArchTest.Rules
- See `docs/regulatory/Circular99-mapping.md` for regulatory compliance mapping
