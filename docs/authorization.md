# Authorization

Role-based access control (RBAC) module for SmeAccounting.

## Module Structure

```
src/Modules/Authorization/
├── Domain/
│   ├── Permissions.cs          # 19 permission constants (6 groups)
│   ├── Roles.cs                # 5 built-in role constants
│   └── RolePermissionMap.cs    # Static role→permissions mapping
├── Application/
│   ├── Authorization/          # Ported policy types
│   │   ├── PermissionRequirement.cs
│   │   ├── PermissionAuthorizationHandler.cs
│   │   ├── PermissionPolicyProvider.cs
│   │   └── ClaimsPrincipalExtensions.cs
│   ├── Commands/               # 6 CQRS commands
│   ├── Queries/                # 3 CQRS queries
│   ├── Validators/             # FluentValidation validators
│   └── AuthorizationApplicationMarker.cs
└── Infrastructure/
    ├── AuthorizationModule.cs
    ├── AuthorizationModuleExtensions.cs
    ├── Services/               # RoleService, PermissionService
    └── Seeding/                # AuthorizationRoleSeeder
```

## Permissions Catalog

19 permissions across 6 groups, defined in `src/Modules/Authorization/Domain/Permissions.cs`:

| Group | Permissions |
|-------|------------|
| Accounts | `accounts.view`, `accounts.create`, `accounts.edit`, `accounts.delete` |
| Journal | `journal.view`, `journal.create`, `journal.edit`, `journal.post`, `journal.reverse` |
| Reports | `reports.view`, `reports.export` |
| Settings | `settings.view`, `settings.manage` |
| Users | `users.view`, `users.create`, `users.edit`, `users.delete`, `users.manage_roles` |
| Audit | `audit.view` |

Format: `module.action` (lowercase). Total: 19.

## Built-in Roles

5 roles defined in `src/Modules/Authorization/Domain/Roles.cs`:

| Role | Description | Permissions |
|------|-------------|-------------|
| Admin | System administrator | All 19 permissions |
| ChiefAccountant | Head of accounting | Accounts + Journal + Reports + Settings (16 perms) |
| Accountant | Regular accountant | Accounts (view/create/edit) + Journal (view/create/edit) + Reports.view (7 perms) |
| Viewer | Read-only access | Accounts.view + Journal.view + Reports.view + Audit.view (4 perms) |
| Auditor | Audit & compliance | Audit.view + Accounts.view + Journal.view + Reports (view/export) (5 perms) |

## Role-Permission Mapping

`RolePermissionMap.cs` provides a static dictionary mapping each role name to its permission set. `GetPermissions(string roleName)` returns the permission list for a role, or an empty list for unknown roles.

Permissions are stored as `"permission"` claims (lowercase) on ASP.NET Core Identity roles via `RoleManager.AddClaimAsync`.

## Role-Claim Storage Model

- **Store**: ASP.NET Core Identity `AspNetRoles` + `AspNetRoleClaims` tables (managed by `IdentityDbContext`)
- **Claim type**: `"permission"` (lowercase literal)
- **Claim value**: permission string (e.g. `accounts.view`)
- **No separate Permission entity**: permissions are a static catalog, not persisted rows
- **No separate Authorization tables**: roles/claims use Identity infrastructure exclusively

## RBAC Pipeline

1. **PermissionPolicyProvider** intercepts policy names starting with `"Permission:"` (case-insensitive) → creates `PermissionRequirement`
2. **PermissionAuthorizationHandler** checks user's `"permission"` claims → grants access if exact match OR if user holds `users.manage_roles` (admin bypass)
3. **Usage**: `[Authorize(Policy = "Permission:accounts.view")]`

```csharp
// In a controller:
[Authorize(Policy = "Permission:accounts.view")]
public IActionResult ViewAccounts() => Ok();
```

## How to Add a Permission

1. Add constant to `src/Modules/Authorization/Domain/Permissions.cs` under the appropriate group:
   ```csharp
   public static class MyGroup
   {
       public const string View = "mygroup.view";
       public const string Create = "mygroup.create";
       public static IReadOnlyList<string> All => [View, Create];
   }
   ```
2. Add permission to `Permissions.All` spread list
3. Update `RolePermissionMap` with role assignments
4. Update `RoleSeeder.StandardRoles` claim seeding in Identity module
5. Use in controllers: `[Authorize(Policy = "Permission:mygroup.view")]`

## How to Attach a Policy

Policies are resolved dynamically by `PermissionPolicyProvider` — no explicit `AddPolicy` registration needed. Any string matching `Permission:*` is handled automatically:

```csharp
// Attribute usage
[Authorize(Policy = "Permission:journal.post")]

// Programmatic usage
if (User.HasPermission(Permissions.Journal.Post))
{
    // proceed
}
```

For non-permission policies, register them via `AddAuthorization` in `Program.cs` as usual.

## CQRS Surface

### Commands (6)

| Command | Description | Handler |
|---------|-------------|---------|
| `CreateRoleCommand` | Create new role with name/description | Delegates to `IRoleService` |
| `DeleteRoleCommand` | Delete built-in role check + removal | Delegates to `IRoleService` |
| `AssignPermissionCommand` | Grant permission to role | Delegates to `IRoleService` |
| `RevokePermissionCommand` | Remove permission from role | Delegates to `IRoleService` |
| `AssignRoleToUserCommand` | Assign role to user by userId | Delegates to `IRoleService` |
| `RemoveRoleFromUserCommand` | Remove role from user | Delegates to `IRoleService` |

### Queries (3)

| Query | Description | Returns |
|-------|-------------|---------|
| `ListRolesQuery` | List all role names | `Result<IReadOnlyList<string>>` |
| `GetRolePermissionsQuery` | Get permissions for a role | `Result<IReadOnlyList<string>>` |
| `GetUserPermissionsQuery` | Get distinct permissions for a user across all roles | `Result<IReadOnlyList<string>>` |

All commands return `Result` (success/failure). Handlers are thin delegates to `IRoleService` / `IPermissionService`.

### Validators

6 FluentValidation validators enforce:
- Role name: `NotEmpty`, `MaxLength(256)`, regex `^[A-Za-z0-9_.-]+$`
- Permission: must be in `Domain.Permissions.All`
- UserId: `NotEmpty`

## API Endpoints

`RolesController` (MVC `Controller` under `[Authorize(Policy = "Permission:users.manage_roles")]`):

| Method | Route | Action |
|--------|-------|--------|
| GET | `/Roles` | List all roles |
| GET | `/Roles/{roleName}/permissions` | Get role permissions |
| POST | `/Roles` | Create role |
| DELETE | `/Roles/{roleName}` | Delete role |
| POST | `/Roles/{roleName}/permissions` | Grant permission |
| DELETE | `/Roles/{roleName}/permissions` | Revoke permission |
| POST | `/Roles/{roleName}/users` | Assign role to user |
| DELETE | `/Roles/{roleName}/users` | Remove role from user |

All endpoints delegate to MediatR. Failures return 400 (BadRequest), never 404.

## Seeding

`AuthorizationRoleSeeder` runs at application startup (Program.cs, non-Testing env):

1. Reconciles permission claims on existing Identity roles (fixes claim drift)
2. Re-assigns admin user to Admin role if missing
3. Idempotent — safe to run on every startup

Seed order: `RoleSeeder` (creates 5 roles) → `UserSeeder` (creates admin) → `AuthorizationRoleSeeder` (reconciles claims).

## Ported Policy Types

Authorization module ports Identity policy types for self-containment:

| Type | Origin | Purpose |
|------|--------|---------|
| `PermissionRequirement` | Identity.Application | `IAuthorizationRequirement` holding permission string |
| `PermissionAuthorizationHandler` | Identity.Application | Evaluates claim-based permission + admin bypass |
| `PermissionPolicyProvider` | Identity.Application | Dynamic `IAuthorizationPolicyProvider` for `Permission:*` prefix |
| `ClaimsPrincipalExtensions` | Identity.Application | `GetUserId`, `HasPermission`, `GetPermissions` helpers |

Identity copies retained for backward compatibility.

## Known Issues

### Guid vs long User IDs

`IRoleService` user methods accept `Guid userId`, but Identity PKs are `long`. Services call `FindByIdAsync(userId.ToString())` which never matches real users — `AssignRoleToUser` / `RemoveRoleFromUser` / `GetUserPermissions` silently return empty/fail. Fix: align service userId type with Identity PK or centralize conversion.

### Dual Auth Stack

- Static 19 policies registered by `AddPermissionPolicies()` (module-level)
- Dynamic `PermissionPolicyProvider` (Identity-level) also intercepts `Permission:*` prefix
- Two `IAuthorizationHandler` registrations (Singleton from Identity, Scoped from Authorization)
- Both succeed on valid permissions (harmless but redundant). Settle single registration site.

### Cross-Module Infrastructure Reference

Authorization.Infrastructure has a `ProjectReference` to Identity.Infrastructure for concrete `ApplicationRole`/`ApplicationUser` types needed by `RoleManager<T>`/`UserManager<T>`. Trades the no-module-refs rule for concrete type requirement. Documented trade-off.

## Source Locations

| Component | Path |
|-----------|------|
| Permissions catalog | `src/Modules/Authorization/Domain/Permissions.cs` |
| Roles constants | `src/Modules/Authorization/Domain/Roles.cs` |
| Role-permission map | `src/Modules/Authorization/Domain/RolePermissionMap.cs` |
| CQRS commands/queries | `src/Modules/Authorization/Application/Commands/`, `Queries/` |
| Validators | `src/Modules/Authorization/Application/Validators/` |
| Policy types | `src/Modules/Authorization/Application/Authorization/` |
| RoleService | `src/Modules/Authorization/Infrastructure/Services/RoleService.cs` |
| PermissionService | `src/Modules/Authorization/Infrastructure/Services/PermissionService.cs` |
| Seeder | `src/Modules/Authorization/Infrastructure/Seeding/AuthorizationRoleSeeder.cs` |
| Controller | `src/SmeAccounting.Api/Controllers/RolesController.cs` |
| Module registration | `src/Modules/Authorization/Infrastructure/AuthorizationModuleExtensions.cs` |
