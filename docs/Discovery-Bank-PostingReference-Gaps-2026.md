# Discovery: Bank/BankBranch/BankAccount Entities and PostingReference Implementation Gaps
Date: 2026-09-22
Loop: implement-gen-acct-02
Task: [G1] Discover missing Bank/BankBranch/BankAccount entities and verify PostingReference implementation gaps

## Summary
Confirmation of absence of Bank domain model and gaps in PostingReference implementation.

## Bank/BankBranch/BankAccount Absence

### Domain Entities
- **Search result:** No entity files found for `Bank`, `BankBranch`, `BankAccount` under `src/SmeAccounting.Domain/Entities/`
- Grep for `class Bank` → only `BankExchangeRateProvider` adapter found at `src/SmeAccounting.Infrastructure/Adapters/BankExchangeRateProvider.cs`
- Grep for `BankAccount` → 0 matches
- Grep for `BankBranch` → 0 matches

### EF Core
- No `BankConfiguration`, `BankBranchConfiguration`, `BankAccountConfiguration` found under `src/SmeAccounting.Infrastructure/Persistence/Configurations/`
- No `DbSet<Bank>` / `DbSet<BankBranch>` / `DbSet<BankAccount>` in `SmeAccountingDbContext`

### Ports & Repositories
- No `IBankRepository`, `IBankBranchRepository`, `IBankAccountRepository` port interfaces in `src/SmeAccounting.Domain/Ports/`
- No repository implementations in `src/SmeAccounting.Infrastructure/Repositories/`

### Application Layer
- No commands/queries/validators for Bank concepts in `src/SmeAccounting.Application/`
- No API controllers for Bank concepts

### Related Existing Artifacts
- `BankExchangeRateProvider` exists as infrastructure adapter implementing `IForeignExchangeRateProvider`. Name collision risk: prefix `Bank` used for service, not entity.
- `PaymentTerm` entity exists with company isolation, but no bank integration.

**Conclusion:** Bank/BankBranch/BankAccount domain model is completely missing.

## PostingReference Implementation Gaps

### Entity Exists But Incomplete
File: `src/SmeAccounting.Domain/Entities/PostingReference.cs`
```csharp
public class PostingReference : BaseEntity
{
    public long JournalEntryId { get; private set; }
    public string SourceType { get; private set; } = string.Empty;
    public long SourceId { get; private set; }
    ...
}
```
- No `CompanyId` property
- No navigation to `JournalEntry`
- Constructor validates `sourceType` via `ArgumentNullException` instead of `DomainException`
- No domain events

### EF Configuration
File: `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingReferenceConfiguration.cs`
- Table `posting_references` with columns `id`, `journal_entry_id`, `source_type`, `source_id`, `xmin`
- Indexes on `journal_entry_id` and `(source_type, source_id)`
- **No FK constraint** to `journal_entries`
- **No CompanyId column**
- No `HasOne<JournalEntry>()` relationship configured
- No `OnDelete` behavior defined

### Migration
Migration `20260916051341_InitialCreate` creates `posting_references` without FK constraint to `journal_entries`.

### DbContext
`SmeAccountingDbContext` exposes `DbSet<PostingReference> PostingReferences` but no configuration for relationship.

### Repository & Application
- No `IPostingReferenceRepository` port interface
- No `EfPostingReferenceRepository` implementation
- No Application commands/queries/validators for PostingReference
- No domain events related to PostingReference

### JournalEntry Coupling
`JournalEntry` entity has `SourceType`/`SourceId` properties and `SetSource` method:
```csharp
public string? SourceType { get; private set; }
public long? SourceId { get; private set; }
public void SetSource(string sourceType, long sourceId) { ... }
```
- `JournalEntry` does not create/manage `PostingReference`
- Source tracking duplicated between `JournalEntry` and `PostingReference` with no synchronization

### Missing Patterns
- No Company isolation: missing `CompanyId` FK with `DeleteBehavior.Restrict`
- No soft-delete `IsActive` flag
- No effective dating
- `SourceType` stored as free string, no enum validation/conversion
- No composite unique index enforcing per-company uniqueness
- No domain validation using `DomainException`
- No repository pattern, no CQRS coverage

**Conclusion:** PostingReference entity exists as a stub with minimal mapping, lacking FK, Company isolation, repository, application layer, domain events, and proper validation.

## Impact
- Bank-related accounting workflows cannot be modeled
- PaymentTerm exists without bank linkage
- PostingReference cannot reliably trace journal entries to source documents
- No audit trail for posting references
- Architecture compliance risk if implemented without following established patterns

## Next Steps
Implement Bank aggregate with Domain entity, EF configuration, repository, Application commands/queries and FluentValidation using TDD per PLAN.md.
