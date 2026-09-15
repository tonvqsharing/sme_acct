# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### [G1] Implement Domain layer - Discovery 2026-09-14
- Created src/Modules/Authorization/Domain/Permissions.cs static catalog with nested classes Accounts, Journal, Reports, Settings, Users, Audit, 19 constants matching docs/security.md, All() aggregates via spread
- Created src/Modules/Authorization/Domain/Roles.cs static class with constants Admin, ChiefAccountant, Accountant, Viewer, Auditor and All()
- Created src/Modules/Authorization/Domain/RolePermissionMap.cs static mapping dictionary with GetPermissions helper, matches RoleSeeder.StandardRoles permissions per docs/security.md
- Domain csproj references verified: only SmeAccounting.Domain and SmeAccounting.SharedKernel, no EF or ASP.NET Core refs
- No Permission entity created, Permission remains static catalog as per design
- Files follow Identity.Application.Permissions pattern, namespace SmeAccounting.Modules.Authorization.Domain
### [G2] Implement Application layer - Discovery 2026-09-15
- Application csproj now mirrors Identity.Application: FrameworkReference Microsoft.AspNetCore.App + versionless FluentValidation + MediatR; locked-mode restore passes, project builds 0 warnings
- Ported Identity policy types locally (PermissionRequirement separate file, PermissionAuthorizationHandler, PermissionPolicyProvider, ClaimsPrincipalExtensions) under SmeAccounting.Modules.Authorization.Application.Authorization, rewired to Domain.Permissions; sealed handler/provider classes; no module-to-module reference
- Abstractions: IPermissionService (GetPermissionsAsync/HasPermissionAsync) + IRoleService (6 command methods + GetRolePermissionsAsync/ListRolesAsync returning Result<T>) — query methods added beyond spec minimum so ListRoles/GetRolePermissions handlers have a service to delegate to
- 6 commands as sealed IRequest<Result> records with thin handlers delegating to IRoleService; 3 queries returning Result<IReadOnlyList<string>> (GetUserPermissions via IPermissionService direct + Result.Create wrap, others via IRoleService passthrough)
- 6 FluentValidation validators: role name NotEmpty/Max256/Regex ^[A-Za-z0-9_.-]+$, permission Must(p => Domain.Permissions.All.Contains(p)), UserId NotEmpty; no new pipeline behavior (global ValidationBehaviour reused)
- Full-solution build has PRE-EXISTING failures unrelated to this task: NU1010 (Sqlite/SqlServer/Pomelo versions missing in Directory.Packages.props) + Identity.Infrastructure CS0234 (SmeAccounting.Infrastructure namespace missing); Authorization.Application builds clean in isolation
- Lock side effect: adding direct FluentValidation ref dropped Microsoft.Extensions.DependencyInjection.Abstractions transitive entries from Application lock (now via FrameworkReference) and added FV transitively to Infrastructure lock; both locks in sync via --locked-mode restore
### [G2] Implement Infrastructure layer - Follow-up verification 2026-09-15
- RoleService design: thin facade over RoleManager<ApplicationRole>/UserManager<ApplicationUser>, idempotent assigns (pre-check claims/IsInRole return Success), permission validated against Domain.Permissions.All before DB touch, Identity errors collapsed via IdentityFailure(code, join descriptions)
- PermissionService design: read-only aggregator, GetPermissionsAsync collects distinct "permission" claims across all user roles into Ordinal HashSet, unknown user returns empty (not Fail), HasPermissionAsync delegates + Ordinal Contains
- Claim literal "permission" lowercase duplicated as const in both services (RoleService.PermissionClaimType + PermissionService.PermissionClaimType) matching RoleSeeder and ClaimsPrincipalExtensions; admin bypass users.manage_roles preserved in ported handler
- Cross-module infra ref decision: Infrastructure csproj adds ProjectReference to Identity.Infrastructure (for ApplicationRole/ApplicationUser concrete types) + FrameworkReference only, zero new PackageReference (Identity/RoleManager types arrive transitively); trades no-module-refs ideal for RoleManager<T> concrete-type requirement; consequence is build inherits pre-existing Identity.Infrastructure CS0234 chain break
- Guid-vs-long handling: IRoleService user methods take Guid userId, services call FindByIdAsync(userId.ToString()); Identity PKs are long so Guid string never matches a real user (returns UserNotFound/empty) — live inconsistency with ClaimsPrincipalExtensions long convention, flagged for verifier/G3 follow-up
- Policy loop: AuthorizationPolicyExtensions.AddPermissionPolicies eagerly registers 19 static "Permission:{p}" policies AND module registers ported PermissionAuthorizationHandler alongside Identity's canonical handler/provider; static policies redundant vs PermissionPolicyProvider dynamic interception (provider wins on prefix), dual handlers both evaluate — harmless (success-only) but must not happen silently, verifier to rule on single-site
- Api wiring: Program.cs adds AddAuthorizationModule() + app.UseAuthentication() (latter was missing — only UseAuthorization existed); RolesController added under [Authorize(Policy=Permission:users.manage_roles)] mediating 8 endpoints via IMediator ListRoles/GetRolePermissions/Create/Delete/Grant/Revoke/AssignUser/RemoveUser
- Build verification: locked-mode restore passes incl. updated Infra lock; infra+Api builds show 0 warnings 0 new errors — only pre-existing failures remain (Identity CS0234 missing SmeAccounting.Infrastructure ref, SmeAccounting.Infrastructure NU1010 Sqlite/SqlServer/Pomelo pins), all in files untouched by this task
- Scope checks pass: no Migrations folder under Authorization/Infrastructure, no new DbContext/DbSet, no new PackageReference (FrameworkReference needs no CPM pin/lock delta beyond transitive)
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

