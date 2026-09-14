# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### [G1] Discover module structure and design domain entities - Discovery 2026-09-14
- Authorization module path verified: src/Modules/Authorization/
- Structure mirrors Identity module: Domain/Application/Infrastructure sub-projects
- Current file inventory:
  - Domain: SmeAccounting.Modules.Authorization.Domain.csproj, packages.lock.json (no source files)
  - Application: SmeAccounting.Modules.Authorization.Application.csproj, packages.lock.json, AuthorizationApplicationMarker.cs
  - Infrastructure: SmeAccounting.Modules.Authorization.Infrastructure.csproj, packages.lock.json, AuthorizationModule.cs, AuthorizationModuleExtensions.cs
- Csproj references:
  - Domain → SmeAccounting.Domain, SmeAccounting.SharedKernel
  - Application → Domain, SmeAccounting.Application, SmeAccounting.SharedKernel, Package MediatR
  - Infrastructure → Application
- AuthorizationModule implements IModule, registers MediatR via RegisterServicesFromAssemblyContaining<AuthorizationApplicationMarker>
- Identity module mirroring confirmed:
  - Identity.Domain contains Role.cs, User.cs; BaseEntity inheritance, Name/NormalizedName/Description/DisplayOrder
  - Identity.Application contains Permissions static catalog, PermissionPolicyProvider, PermissionAuthorizationHandler, ClaimsPrincipalExtensions
  - Identity.Infrastructure contains ApplicationUser/ApplicationRole extending Identity classes, IdentityDbContext with snake_case naming, RoleSeeder, UserSeeder
- Permissions static catalog design assumptions:
  - Location: SmeAccounting.Modules.Identity.Application.Permissions
  - Static class with nested static classes Accounts, Journal, Reports, Settings, Users, Audit
  - Constants format "module.action", 19 total permissions
  - Each group exposes All IReadOnlyList<string>, root All aggregates via spread
  - Policy prefix "Permission:" used in Authorization, claim type "permission"
  - Admin bypass via Users.ManageRoles permission in PermissionAuthorizationHandler
- Roles constants design assumptions:
  - StandardRoles defined in RoleSeeder.StandardRoles as readonly tuple array (Name, Description, Permissions)
  - Roles: Admin, ChiefAccountant, Accountant, Viewer, Auditor
  - Admin gets Permissions.All
  - ChiefAccountant: Accounts.All + Journal.All + Reports.All + Settings.All
  - Accountant: Accounts.View/Create/Edit + Journal.View/Create/Edit + Reports.View
  - Viewer: Accounts.View + Journal.View + Reports.View + Audit.View
  - Auditor: Audit.View + Accounts.View + Journal.View + Reports.View/Export
  - Roles seeded via ASP.NET Core Identity RoleManager with permission claims
- RolePermissionMap design assumptions:
  - No existing persisted Permission entity; Permission is static catalog
  - Authorization module intended to provide domain entities Role, Permission, RolePermission aggregate separate from Identity ASP.NET Core tables
  - Expected domain entities: Role aggregate root inheriting BaseEntity with Name, NormalizedName, Description, DisplayOrder, IsBuiltIn flag
  - RolePermissionMap entity links RoleId long FK to Permission string value
  - Value objects for Permission string validation possible
  - Domain events: RoleCreated, RoleUpdated, RoleDeleted, PermissionAssigned, PermissionRemoved
  - Domain must stay free of EF Core/ASP.NET Core, follow BaseEntity, IAuditable, ISoftDeletable, ICompanyScoped conventions, snake_case DB naming via EF converter, bigint identity PKs, xmin concurrency
- Design constraints captured:
  - Clean Architecture layer rules enforced
  - Module registration explicit via AddModules([...])
  - No module-to-module project references
  - FrameworkReference Microsoft.AspNetCore.App required for ASP.NET Core services in net10.0 libs
  - Permissions catalog must match docs/security.md 19 permissions, 5 roles

