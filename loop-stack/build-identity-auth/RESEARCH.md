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

## Task-Specific Research — Task 4

### Source files to copy

#### ApplicationUser.cs (`src/SmeAccounting.Infrastructure/Identity/ApplicationUser.cs`)
- Extends `IdentityUser<long>` (Microsoft.AspNetCore.Identity)
- Custom properties: `DisplayName` (string), `BranchId` (long?), `IsEnabled` (bool, default true), `CreatedAtUtc` (DateTime, default UtcNow), `LastLoginAtUtc` (DateTime?)
- Namespace: `SmeAccounting.Infrastructure.Identity` → `SmeAccounting.Modules.Identity.Infrastructure`
- Simple copy, only namespace changes

#### ApplicationRole.cs (`src/SmeAccounting.Infrastructure/Identity/ApplicationRole.cs`)
- Extends `IdentityRole<long>` (Microsoft.AspNetCore.Identity)
- Custom properties: `Description` (string), `DisplayOrder` (int)
- Namespace: `SmeAccounting.Infrastructure.Identity` → `SmeAccounting.Modules.Identity.Infrastructure`
- Simple copy, only namespace changes

### Domain entities to map TO

#### User.cs (`src/Modules/Identity/Domain/User.cs`)
- Extends `BaseEntity` (SharedKernel) — `long Id` from base
- Properties: `DisplayName`, `Email`, `UserName`, `BranchId` (long?), `IsEnabled` (bool), `CreatedAtUtc` (DateTime), `LastLoginAtUtc` (DateTime?), `PasswordHash` (string?), `FailedLoginAttempts` (int), `LockedUntilUtc` (DateTimeOffset?)
- Computed: `IsLockedOut` (bool)
- Methods: `RecordSuccessfulLogin`, `RecordFailedLogin`, `Lock`, `Unlock`, `SetPasswordHash`, `Deactivate`, `Activate`
- Protected parameterless constructor

#### Role.cs (`src/Modules/Identity/Domain/Role.cs`)
- Extends `BaseEntity` (SharedKernel) — `long Id` from base
- Properties: `Name`, `NormalizedName`, `Description`, `DisplayOrder` (int)
- Protected parameterless constructor

### Mapper design (ApplicationUserMapper.cs)

**To create**: `src/Modules/Identity/Infrastructure/ApplicationUserMapper.cs`

#### `static User ToDomain(ApplicationUser appUser)` mapping:
| ApplicationUser (IdentityUser<long> + custom) | Domain User (BaseEntity + custom) | Notes |
|---|---|---|
| `appUser.Id` | `user.Id` | From `IdentityUser<long>` base |
| `appUser.DisplayName` | `user.DisplayName` | Custom property |
| `appUser.Email` | `user.Email` | From `IdentityUser<long>` base |
| `appUser.UserName` | `user.UserName` | From `IdentityUser<long>` base |
| `appUser.BranchId` | `user.BranchId` | Custom property |
| `appUser.IsEnabled` | `user.IsEnabled` | Custom property |
| `appUser.CreatedAtUtc` | `user.CreatedAtUtc` | Custom property |
| `appUser.LastLoginAtUtc` | `user.LastLoginAtUtc` | Custom property |

**Not mapped** (Identity-managed, domain has its own):
- `PasswordHash` — domain `User` stores it separately via `SetPasswordHash()`
- `FailedLoginAttempts`, `LockedUntilUtc` — domain manages lockout state via methods
- `IsLockedOut` — computed from `LockedUntilUtc`

#### `static Role ToDomain(ApplicationRole appRole)` mapping:
| ApplicationRole (IdentityRole<long> + custom) | Domain Role (BaseEntity + custom) |
|---|---|
| `appRole.Id` | `role.Id` |
| `appRole.Name` | `role.Name` |
| `appRole.NormalizedName` | `role.NormalizedName` |
| `appRole.Description` | `role.Description` |
| `appRole.DisplayOrder` | `role.DisplayOrder` |

### Mapper creates new domain entities (not updating existing)
- Domain entities have protected parameterless constructors — mapper calls `new User()` and `new Role()`
- Mapper is static, stateless — no DI needed
- Uses `SmeAccounting.Modules.Identity.Domain` namespace for return types
- Uses `SmeAccounting.Modules.Identity.Infrastructure` namespace for source types

### Dependencies check
- Infrastructure csproj already has ProjectReference to Domain (Task 3)
- Infrastructure csproj already has FrameworkReference to Microsoft.AspNetCore.App (Task 3)
- No new packages needed
- No new project references needed

### Files to create (3 total)
1. `src/Modules/Identity/Infrastructure/ApplicationUser.cs` — copy, change namespace
2. `src/Modules/Identity/Infrastructure/ApplicationRole.cs` — copy, change namespace
3. `src/Modules/Identity/Infrastructure/ApplicationUserMapper.cs` — new static mapper class

### csproj changes
- None needed (all references already in place from Task 3)

### Build impact
- After this task: IdentityDbContext.cs compiles (ApplicationUser/ApplicationRole now defined)
- Remaining build errors should be zero (unless Task 5 items still pending)

## Task-Specific Research — Task 5

### Overview
Wire DI, add seeders, remove old centralized identity code. Depends on Tasks 2+4 (all Application and Infrastructure types exist).

### Files to copy (2)

#### RoleSeeder.cs (`src/SmeAccounting.Infrastructure/Identity/RoleSeeder.cs`)
- 58 lines, static class `RoleSeeder`
- `StandardRoles` array: 5 roles (Admin, ChiefAccountant, Accountant, Viewer, Auditor) with permission lists
- `SeedAsync(RoleManager<ApplicationRole>, ILogger)` — creates roles + permission claims
- Uses `Permissions` (from `SmeAccounting.Modules.Identity.Application` — Task 2)
- Uses `ApplicationRole` (same Infrastructure namespace — Task 4)
- **Namespace change**: `SmeAccounting.Infrastructure.Identity` → `SmeAccounting.Modules.Identity.Infrastructure`
- **Using add**: `using SmeAccounting.Modules.Identity.Application;` (for `Permissions`)
- Target: `src/Modules/Identity/Infrastructure/RoleSeeder.cs`

#### UserSeeder.cs (`src/SmeAccounting.Infrastructure/Identity/UserSeeder.cs`)
- 44 lines, static class `UserSeeder`
- `SeedAsync(UserManager<ApplicationUser>, RoleManager<ApplicationRole>, ILogger, string?)` — creates admin user
- Uses `ApplicationUser` and `ApplicationRole` (same namespace after copy)
- **Namespace change**: `SmeAccounting.Infrastructure.Identity` → `SmeAccounting.Modules.Identity.Infrastructure`
- Target: `src/Modules/Identity/Infrastructure/UserSeeder.cs`

### IdentityModule.cs — rewrite

Current state (12 lines): only MediatR registration via `IdentityApplicationMarker`.

New design:
```csharp
public sealed class IdentityModule : IModule
{
    private readonly IConfiguration _configuration;

    public IdentityModule(IConfiguration configuration)
        => _configuration = configuration;

    public IServiceCollection AddModule(IServiceCollection services)
    {
        // Identity DbContext
        services.AddDbContext<IdentityDbContext>(options =>
            options.UseNpgsql(_configuration.GetConnectionString("DefaultConnection")));

        // ASP.NET Identity
        services.AddIdentity<ApplicationUser, ApplicationRole>(options => { ... })
            .AddEntityFrameworkStores<IdentityDbContext>()
            .AddDefaultTokenProviders();

        // Cookie policy
        services.ConfigureApplicationCookie(options => { ... });

        // Permission authorization
        services.AddSingleton<IAuthorizationPolicyProvider, PermissionPolicyProvider>();
        services.AddScoped<IAuthorizationHandler, PermissionAuthorizationHandler>();

        // MediatR
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<IdentityApplicationMarker>());

        return services;
    }
}
```

Key decisions:
- `IConfiguration` injected via constructor (not `IServiceProvider` — avoids building provider early)
- All Identity config from `IdentityServiceExtensions.AddIdentityInfrastructure()` moves here verbatim
- Seeders NOT executed in `AddModule` — that runs during DI composition (too early for scoped services). Seeders should run at app startup via a separate mechanism (e.g., `IHostedService` or middleware). Plan says "call during AddModule" but that's incorrect for scoped `UserManager`/`RoleManager`. Better: add a static `SeedAsync` method that can be called from Program.cs after build, or use a scoped service. **Executor should resolve this.**

### IdentityModuleExtensions.cs — update

Current: `AddIdentityModule()` no args.
New: `AddIdentityModule(IConfiguration configuration)` passes config to constructor.

### IConfiguration parameter threading

`IModule.AddModule(IServiceCollection)` doesn't accept `IConfiguration`. Options:
1. **Constructor injection** (chosen) — `new IdentityModule(builder.Configuration)` in Program.cs
2. `IServiceProvider` in `AddModule` — bad practice (building provider early)

Program.cs change: `new IdentityModule()` → `new IdentityModule(builder.Configuration)`

### Files to delete (11) from `src/SmeAccounting.Infrastructure/Identity/`

| File | Reason |
|---|---|
| `ApplicationRole.cs` | Moved to Module Infrastructure (Task 4) |
| `ApplicationUser.cs` | Moved to Module Infrastructure (Task 4) |
| `ClaimsPrincipalExtensions.cs` | Moved to Module Application (Task 2) |
| `IdentityDbContext.cs` | Moved to Module Infrastructure (Task 3) |
| `IdentityDbContextFactory.cs` | Moved to Module Infrastructure (Task 3) |
| `IdentityServiceExtensions.cs` | Logic absorbed into IdentityModule.cs |
| `PermissionAuthorizationHandler.cs` | Moved to Module Application (Task 2) |
| `PermissionPolicyProvider.cs` | Moved to Module Application (Task 2) |
| `Permissions.cs` | Moved to Module Application (Task 2) |
| `RoleSeeder.cs` | Moving to Module Infrastructure (Task 5) |
| `UserSeeder.cs` | Moving to Module Infrastructure (Task 5) |

### DependencyInjection.cs changes

Remove from `src/SmeAccounting.Infrastructure/DependencyInjection.cs`:
- Line 9: `using SmeAccounting.Infrastructure.Identity;`
- Line 47: `services.AddIdentityInfrastructure(configuration);`

After removal, no remaining code in base Infrastructure references the Identity namespace.

### Base Infrastructure csproj cleanup

`src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj` has:
- `<PackageReference Include="Microsoft.AspNetCore.Identity.EntityFrameworkCore" />` — can remove (no remaining Identity code in base Infrastructure)

Verify: grep confirms all `IdentityDbContext`/`UserManager`/`RoleManager` refs are within `Identity/` subfolder only.

### AccountsController.cs — using update required

`src/SmeAccounting.Api/Controllers/AccountsController.cs` (line 5):
- `using SmeAccounting.Infrastructure.Identity;` → `using SmeAccounting.Modules.Identity.Infrastructure;`
- Uses `ApplicationUser` in `SignInManager<ApplicationUser>` and `UserManager<ApplicationUser>` constructor params

### Program.cs changes

`src/SmeAccounting.Api/Program.cs` line 30:
- `new IdentityModule()` → `new IdentityModule(builder.Configuration)`

### Dependency chain summary

| Action | File | What changes |
|---|---|---|
| CREATE | `Modules/Identity/Infrastructure/RoleSeeder.cs` | Copy + namespace + using |
| CREATE | `Modules/Identity/Infrastructure/UserSeeder.cs` | Copy + namespace |
| REWRITE | `Modules/Identity/Infrastructure/IdentityModule.cs` | Full Identity setup + IConfiguration ctor |
| UPDATE | `Modules/Identity/Infrastructure/IdentityModuleExtensions.cs` | Accept IConfiguration |
| UPDATE | `SmeAccounting.Api/Program.cs` | Pass config to IdentityModule |
| UPDATE | `SmeAccounting.Api/Controllers/AccountsController.cs` | Using namespace change |
| UPDATE | `SmeAccounting.Infrastructure/DependencyInjection.cs` | Remove Identity using + call |
| UPDATE | `SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj` | Remove Identity.EntityFrameworkCore pkg |
| DELETE | `SmeAccounting.Infrastructure/Identity/*` (11 files) | All moved or absorbed |

### Build risk
- After deleting old Identity files + updating using statements, build should succeed IF all namespace changes are correct
- Missing namespace change in AccountsController would cause CS0246 (type not found)
- Missing IConfiguration in IdentityModule constructor would cause runtime DI error, not build error
