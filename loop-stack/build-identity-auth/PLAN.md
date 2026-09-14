# Loop Plan
## Mode
build
## Goal
Replace marker-only Identity stub with complete cookie-based authentication system in SmeAccounting.Modules.Identity using ASP.NET Core / EF Core / Npgsql built-in packages on net10.0 LTS following Clean Architecture + Modular Monolith conventions
## Stop Condition
all tasks in loop-stack/build-identity-auth/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks

- [x] [G1] **Task 1: Domain entities for Identity** ✅ VERIFIED_PASS
  Create `User` and `Role` domain entities in `src/Modules/Identity/Domain/`. These are pure domain types — NO reference to `Microsoft.AspNetCore.Identity`.
  - `User.cs` (`BaseEntity`): `DisplayName`, `Email`, `UserName`, `BranchId` (long?), `IsEnabled` (bool), `CreatedAtUtc`, `LastLoginAtUtc` (DateTime?)
  - `Role.cs` (`BaseEntity`): `Name`, `NormalizedName`, `Description`, `DisplayOrder` (int)
  - Leave `SmeAccounting.Modules.Identity.Domain.csproj` unchanged (keeps references to `SmeAccounting.Domain` and `SmeAccounting.SharedKernel` — `BaseEntity` lives in SharedKernel)

- [x] [G2] **Task 2: Application layer — Permissions, ClaimsPrincipalExtensions, Authorization** ✅ VERIFIED_PASS
  Move permission constants and authorization logic into the Application layer. NO dependency on Infrastructure.
  - `Permissions.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/Permissions.cs` → `src/Modules/Identity/Application/Permissions.cs`. Change namespace to `SmeAccounting.Modules.Identity.Application`.
  - `ClaimsPrincipalExtensions.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/ClaimsPrincipalExtensions.cs` → `src/Modules/Identity/Application/ClaimsPrincipalExtensions.cs`. Change namespace to `SmeAccounting.Modules.Identity.Application`.
  - `PermissionRequirement.cs` + `PermissionAuthorizationHandler.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/PermissionAuthorizationHandler.cs` → `src/Modules/Identity/Application/PermissionAuthorizationHandler.cs`. Change namespace to `SmeAccounting.Modules.Identity.Application`.
  - `PermissionPolicyProvider.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/PermissionPolicyProvider.cs` → `src/Modules/Identity/Application/PermissionPolicyProvider.cs`. Change namespace to `SmeAccounting.Modules.Identity.Application`.
  - Update `SmeAccounting.Modules.Identity.Application.csproj`: add `<FrameworkReference Include="Microsoft.AspNetCore.App" />` (needed for `Microsoft.AspNetCore.Authorization` types used by PermissionPolicyProvider and PermissionAuthorizationHandler)

- [x] [G2] **Task 3: Infrastructure project setup and IdentityDbContext** ✅ VERIFIED_PASS
  Prepare Infrastructure layer with required packages and database context.
  - Update `SmeAccounting.Modules.Identity.Infrastructure.csproj`:
    - Add `<FrameworkReference Include="Microsoft.AspNetCore.App" />`
    - Add PackageReferences: `Microsoft.AspNetCore.Identity.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Design`, `Npgsql.EntityFrameworkCore.PostgreSQL`
    - Add ProjectReference: `../Domain/SmeAccounting.Modules.Identity.Domain.csproj`
  - `IdentityDbContext.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/IdentityDbContext.cs` → `src/Modules/Identity/Infrastructure/IdentityDbContext.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`.
  - `IdentityDbContextFactory.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/IdentityDbContextFactory.cs` → `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`.

- [x] [G3] **Task 4: Infrastructure — ApplicationUser, ApplicationRole, and mapper**
  Create Identity types and the mapper to/from domain entities. Depends on Task 1 (Domain entities) and Task 3 (Infrastructure project setup).
  - `ApplicationUser.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/ApplicationUser.cs` → `src/Modules/Identity/Infrastructure/ApplicationUser.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`.
  - `ApplicationRole.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/ApplicationRole.cs` → `src/Modules/Identity/Infrastructure/ApplicationRole.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`.
  - Create `ApplicationUserMapper.cs` in `src/Modules/Identity/Infrastructure/`:
    - `static User ToDomain(ApplicationUser appUser)` — maps `Id`, `DisplayName`, `Email`, `UserName`, `BranchId`, `IsEnabled`, `CreatedAtUtc`, `LastLoginAtUtc` to `SmeAccounting.Modules.Identity.Domain.User`
    - `static Role ToDomain(ApplicationRole appRole)` — maps `Id`, `Name`, `NormalizedName`, `Description`, `DisplayOrder` to `SmeAccounting.Modules.Identity.Domain.Role`

- [x] [G3] **Task 5: Infrastructure — seeders, module wiring, and cleanup** ✅ VERIFIED_PASS
  Wire DI, add seeders, and remove old centralized identity code. Depends on Tasks 2+4 (all Application and Infrastructure types).
  - `RoleSeeder.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/RoleSeeder.cs` → `src/Modules/Identity/Infrastructure/RoleSeeder.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`. Update `using` for `Permissions` to `SmeAccounting.Modules.Identity.Application`.
  - `UserSeeder.cs` — copy from `src/SmeAccounting.Infrastructure/Identity/UserSeeder.cs` → `src/Modules/Identity/Infrastructure/UserSeeder.cs`. Change namespace to `SmeAccounting.Modules.Identity.Infrastructure`.
  - Update `IdentityModule.cs`:
    - Add `AddIdentityInfrastructure(configuration)` call (move from base Infrastructure DependencyInjection.cs) — the IdentityDbContext registration, ASP.NET Identity configuration, cookie policy, permission auth setup all go here
    - Add seeder execution: resolve `RoleManager<ApplicationRole>` and `UserManager<ApplicationUser>` from service provider, call `RoleSeeder.SeedAsync()` and `UserSeeder.SeedAsync()` during `AddModule()`
    - Keep existing MediatR registration
    - `AddModule` signature may need `IServiceProvider` or use a pattern to get configuration — check how other modules pass configuration (or accept `IConfiguration` via constructor)
  - Update `IdentityModuleExtensions.cs` to accept `IConfiguration` parameter and pass it through
  - Remove old files from `src/SmeAccounting.Infrastructure/Identity/` (all 11 files)
  - Remove `using SmeAccounting.Infrastructure.Identity;` and `services.AddIdentityInfrastructure(configuration);` from `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
  - Update `src/SmeAccounting.Api/Program.cs` if needed to pass `IConfiguration` to `AddIdentityModule()`
