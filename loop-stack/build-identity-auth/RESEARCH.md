# Research — build-identity-auth

## Task-Specific Research — Task 1

### BaseEntity (`src/SmeAccounting.SharedKernel/Primitives/BaseEntity.cs`)
- `long Id` (public get/set) — auto-assigned by EF
- `IReadOnlyCollection<IDomainEvent> DomainEvents` — domain event collection
- `RaiseDomainEvent(IDomainEvent)` / `ClearDomainEvents()` methods
- Protected parameterless constructor

### IAuditable (`src/SmeAccounting.SharedKernel/Primitives/IAuditable.cs`)
- `CreatedAtUtc`, `CreatedBy` (Guid?), `UpdatedAtUtc`, `UpdatedBy` (Guid?)
- User goal only specifies `CreatedAtUtc` — do NOT implement IAuditable (would force extra fields)

### IDateTimeProvider (`src/SmeAccounting.SharedKernel/Abstractions/IDateTimeProvider.cs`)
- `DateTime UtcNow { get; }` — use this instead of IClock from the goal

### Existing entity patterns (Company.cs, Branch.cs)
- Extend `BaseEntity`, implement interfaces explicitly with `{ get; set; } = default!;`
- No field initializers on string props (use `= default!;`)
- Navigation props as nullable `ICollection<T>` or `T?`

### Identity stubs (existing)
- `ApplicationUser : IdentityUser<long>` — DisplayName, BranchId, IsEnabled, CreatedAtUtc, LastLoginAtUtc
- `ApplicationRole : IdentityRole<long>` — Description, DisplayOrder
- Domain entities must mirror these fields WITHOUT referencing Microsoft.AspNetCore.Identity

### Domain csproj
- References `SmeAccounting.Domain` and `SmeAccounting.SharedKernel` — no changes needed

### Namespace convention
- `SmeAccounting.Modules.Identity.Domain`
