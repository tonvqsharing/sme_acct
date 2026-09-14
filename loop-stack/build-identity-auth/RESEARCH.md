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

## Task-Specific Research — Task 2

### Source files to copy

#### Permissions.cs (`src/SmeAccounting.Infrastructure/Identity/Permissions.cs`)
- Static class with nested static classes for 6 permission groups: Accounts, Journal, Reports, Settings, Users, Audit
- 19 total permission constants (string literals like `"accounts.view"`)
- Each group has an `All` property (`IReadOnlyList<string>`) collecting its constants
- Top-level `All` aggregates all groups using spread operator (`.. Accounts.All`)
- No external dependencies — pure constants

#### ClaimsPrincipalExtensions.cs (`src/SmeAccounting.Infrastructure/Identity/ClaimsPrincipalExtensions.cs`)
- Extension methods on `System.Security.Claims.ClaimsPrincipal`
- `GetUserId()` → `long?` via `ClaimTypes.NameIdentifier`
- `GetDisplayName()` → `string?` via `"display_name"` or `ClaimTypes.Name`
- `GetBranchId()` → `long?` via `"branch_id"`
- `GetPermissions()` → `IReadOnlyList<string>` via `"permission"` claim
- `HasPermission(string)` → `bool`
- Dependencies: `System.Security.Claims` (already available in net10.0)

#### PermissionAuthorizationHandler.cs (`src/SmeAccounting.Infrastructure/Identity/PermissionAuthorizationHandler.cs`)
- Two types in one file:
  - `PermissionRequirement : IAuthorizationRequirement` — holds `string Permission`
  - `PermissionAuthorizationHandler : AuthorizationHandler<PermissionRequirement>` — checks if user has the required permission OR `Users.ManageRoles` (admin bypass)
- Dependencies: `Microsoft.AspNetCore.Authorization` → needs `<FrameworkReference Include="Microsoft.AspNetCore.App" />`

#### PermissionPolicyProvider.cs (`src/SmeAccounting.Infrastructure/Identity/PermissionPolicyProvider.cs`)
- `IAuthorizationPolicyProvider` implementation
- Intercepts policy names starting with `"Permission:"` prefix → creates policy with `PermissionRequirement`
- Falls back to `DefaultAuthorizationPolicyProvider` for standard policies
- Dependencies: `Microsoft.AspNetCore.Authorization`, `Microsoft.Extensions.Options` → needs `<FrameworkReference Include="Microsoft.AspNetCore.App" />`

### Current Application csproj
- References: `SmeAccounting.Modules.Identity.Domain`, `SmeAccounting.Application`, `SmeAccounting.SharedKernel`
- Package refs: `MediatR` only
- **Missing**: `<FrameworkReference Include="Microsoft.AspNetCore.App" />` — required for Authorization types

### SharedKernel types relevant to Application layer
- `ICurrentUserProvider` — `Guid? UserId`, `bool IsAuthenticated` — in `SmeAccounting.SharedKernel` namespace
- No other claims/permissions interfaces in SharedKernel
- `ICurrentUserProvider` is NOT used by the 4 files being moved; it's a separate concern for future use

### Namespace mapping
| Source (Infrastructure) | Target (Application) |
|---|---|
| `SmeAccounting.Infrastructure.Identity` | `SmeAccounting.Modules.Identity.Application` |

### Files to create (4 total)
1. `src/Modules/Identity/Application/Permissions.cs` — copy, change namespace
2. `src/Modules/Identity/Application/ClaimsPrincipalExtensions.cs` — copy, change namespace
3. `src/Modules/Identity/Application/PermissionAuthorizationHandler.cs` — copy, change namespace
4. `src/Modules/Identity/Application/PermissionPolicyProvider.cs` — copy, change namespace

### csproj change
- Add `<FrameworkReference Include="Microsoft.AspNetCore.App" />` to `SmeAccounting.Modules.Identity.Application.csproj`

### No SharedKernel changes needed
- The 4 files only depend on `System.Security.Claims` and `Microsoft.AspNetCore.Authorization`
- `ICurrentUserProvider` is orthogonal — not referenced by any of these files

## Task-Specific Research — Task 3

### Current Infrastructure csproj (`src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj`)
- Only has one ProjectReference: `../Application/SmeAccounting.Modules.Identity.Application.csproj`
- No FrameworkReference, no PackageReferences
- RootNamespace and AssemblyName already set correctly

### Source IdentityDbContext.cs (`src/SmeAccounting.Infrastructure/Identity/IdentityDbContext.cs`)
- Extends `IdentityDbContext<ApplicationUser, ApplicationRole, long>` (Microsoft.AspNetCore.Identity.EntityFrameworkCore)
- OnModelCreating: snake_case conversion for all table names and column names
- Private `ToSnakeCase(string)` helper inserts `_` before uppercase chars
- Namespace: `SmeAccounting.Infrastructure.Identity` → change to `SmeAccounting.Modules.Identity.Infrastructure`

### Source IdentityDbContextFactory.cs (`src/SmeAccounting.Infrastructure/Identity/IdentityDbContextFactory.cs`)
- `IDesignTimeDbContextFactory<IdentityDbContext>` (Microsoft.EntityFrameworkCore.Design)
- Hardcoded Npgsql connection string: `Host=localhost;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres`
- Namespace: `SmeAccounting.Infrastructure.Identity` → change to `SmeAccounting.Modules.Identity.Infrastructure`

### Directory.Packages.props — existing package versions
| Package | Version | Needed? |
|---|---|---|
| `Microsoft.AspNetCore.Identity.EntityFrameworkCore` | 10.0.12 | YES |
| `Microsoft.EntityFrameworkCore` | 10.0.12 | YES |
| `Microsoft.EntityFrameworkCore.Design` | 10.0.12 | YES (for factory) |
| `Npgsql.EntityFrameworkCore.PostgreSQL` | 10.0.3 | YES |

All 4 packages already pinned in Directory.Packages.props — no new CPM entries needed.

### Base Infrastructure csproj pattern (`src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj`)
- Has `<FrameworkReference Include="Microsoft.AspNetCore.App" />`
- PackageRefs: `Microsoft.AspNetCore.Identity.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore`, `Npgsql.EntityFrameworkCore.PostgreSQL`
- Does NOT include `Microsoft.EntityFrameworkCore.Design` (only in Directory.Packages.props for design-time)
- Pattern: versionless `<PackageReference Include="..." />` under CPM

### csproj changes needed
Add to `SmeAccounting.Modules.Identity.Infrastructure.csproj`:
1. `<FrameworkReference Include="Microsoft.AspNetCore.App" />` — needed for `IdentityDbContext<>` base class and ASP.NET Identity types
2. PackageReferences (versionless, CPM-managed):
   - `Microsoft.AspNetCore.Identity.EntityFrameworkCore`
   - `Microsoft.EntityFrameworkCore`
   - `Microsoft.EntityFrameworkCore.Design`
   - `Npgsql.EntityFrameworkCore.PostgreSQL`
3. ProjectReference: `../Domain/SmeAccounting.Modules.Identity.Domain.csproj`

### Dependency consideration
- `IdentityDbContext` references `ApplicationUser` and `ApplicationRole` — these are in the SAME Infrastructure project (Task 4 creates them)
- This means IdentityDbContext.cs will reference types not yet defined at Task 3 time — normal for incremental implementation; won't compile until Task 4 adds them
- Alternative: defer file creation until Task 4. But plan says Task 3 creates them, so follow plan.

### Files to create (2 total)
1. `src/Modules/Identity/Infrastructure/IdentityDbContext.cs` — copy, change namespace
2. `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs` — copy, change namespace

### Namespace mapping
| Source (Infrastructure) | Target (Module Infrastructure) |
|---|---|
| `SmeAccounting.Infrastructure.Identity` | `SmeAccounting.Modules.Identity.Infrastructure` |
