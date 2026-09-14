# Security

## Identity

ASP.NET Core Identity with cookie authentication.

### Configuration

`src/SmeAccounting.Infrastructure/Identity/IdentityServiceExtensions.cs`:

```csharp
options.Password.RequireDigit = true;
options.Password.RequireLowercase = true;
options.Password.RequireUppercase = true;
options.Password.RequireNonAlphanumeric = true;
options.Password.RequiredLength = 8;
options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
options.Lockout.MaxFailedAccessAttempts = 5;
options.User.RequireUniqueEmail = true;
options.SignIn.RequireConfirmedEmail = true;
```

### Cookie Settings

| Setting | Value |
|---------|-------|
| LoginPath | `/Accounts/Login` |
| LogoutPath | `/Accounts/Logout` |
| AccessDeniedPath | `/Accounts/AccessDenied` |
| ExpireTimeSpan | 8 hours |
| SlidingExpiration | true |
| HttpOnly | true |
| SameSite | Lax |
| SecurePolicy | SameAsRequest |

### User/Role Models

- `ApplicationUser` (`src/SmeAccounting.Infrastructure/Identity/ApplicationUser.cs`) — extends `IdentityUser<long>` with `DisplayName`, `BranchId`, `IsEnabled`, `CreatedAtUtc`, `LastLoginAtUtc`
- `ApplicationRole` (`src/SmeAccounting.Infrastructure/Identity/ApplicationRole.cs`) — extends `IdentityRole<long>` with `Description`, `DisplayOrder`

### Identity DbContext

Separate `IdentityDbContext` (`src/SmeAccounting.Infrastructure/Identity/IdentityDbContext.cs`) for ASP.NET Core Identity tables. Also applies snake_case naming.

## RBAC

### Permissions

19 permissions defined in `src/SmeAccounting.Infrastructure/Identity/Permissions.cs`:

| Group | Permissions |
|-------|------------|
| Accounts | `accounts.view`, `accounts.create`, `accounts.edit`, `accounts.delete` |
| Journal | `journal.view`, `journal.create`, `journal.edit`, `journal.post`, `journal.reverse` |
| Reports | `reports.view`, `reports.export` |
| Settings | `settings.view`, `settings.manage` |
| Users | `users.view`, `users.create`, `users.edit`, `users.delete`, `users.manage_roles` |
| Audit | `audit.view` |

### Roles

5 roles seeded by `RoleSeeder` (`src/SmeAccounting.Infrastructure/Identity/RoleSeeder.cs`):

| Role | Description | Permissions |
|------|-------------|-------------|
| Admin | System administrator | All 19 permissions |
| ChiefAccountant | Head of accounting | Accounts + Journal + Reports + Settings |
| Accountant | Regular accountant | Accounts (view/create/edit) + Journal (view/create/edit) + Reports.view |
| Viewer | Read-only access | Accounts.view + Journal.view + Reports.view + Audit.view |
| Auditor | Audit & compliance | Audit.view + Accounts.view + Journal.view + Reports (view/export) |

Permissions stored as `"permission"` claims on roles.

### Authorization Pipeline

1. `PermissionPolicyProvider` (`src/SmeAccounting.Infrastructure/Identity/PermissionPolicyProvider.cs`) — intercepts policy names starting with `"Permission:"` and creates `PermissionRequirement`
2. `PermissionAuthorizationHandler` (`src/SmeAccounting.Infrastructure/Identity/PermissionAuthorizationHandler.cs`) — checks user's `permission` claims; also grants access to `users.manage_roles` holders
3. Usage in controllers: `[Authorize(Policy = "Permission:accounts.view")]`

### Claims Principal Extensions

`src/SmeAccounting.Infrastructure/Identity/ClaimsPrincipalExtensions.cs`:

- `GetUserId()` — parses `ClaimTypes.NameIdentifier`
- `GetDisplayName()` — reads `display_name` claim
- `GetBranchId()` — reads `branch_id` claim
- `GetPermissions()` — returns all `permission` claims
- `HasPermission(string)` — checks specific permission

## Default Seeded User

| Field | Value |
|-------|-------|
| Email | admin@smeaccounting.vn |
| Username | admin |
| Password | Admin@12345 (override via `ADMIN_PASSWORD` env var) |
| EmailConfirmed | true |
| Role | Admin |

See `src/SmeAccounting.Infrastructure/Identity/UserSeeder.cs`.

## Data Protection

```csharp
services.AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo(
        configuration["Security:DataProtectionPath"] ?? "./dataprotection-keys"))
    .SetApplicationName("SmeAccounting");
```

Keys persisted to local filesystem. For multi-instance deployments, use Azure Blob Storage, Redis, or database-backed key ring.

## Security Headers

`SecurityHeadersMiddleware` (`src/SmeAccounting.Infrastructure/Security/SecurityHeadersMiddleware.cs`):

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Content-Security-Policy | default-src 'self' |
| Strict-Transport-Security | max-age=31536000; includeSubDomains (excludes /health) |

## Antiforgery

ASP.NET Core default antiforgery tokens enabled via MVC's `AddControllersWithViews()`. Tokens validated on form submissions.

## Forwarded Headers

`ForwardedHeadersServiceExtensions` — configures `ForwardedHeadersOptions` for reverse proxy (Nginx) deployments. Supports `X-Forwarded-For` and `X-Forwarded-Proto`.

## Global Exception Handling

`GlobalExceptionMiddleware` (`src/SmeAccounting.Infrastructure/ErrorHandling/`) catches unhandled exceptions and returns structured error responses. Registered via `app.UseGlobalExceptionHandler()`.

## Security Options

`src/SmeAccounting.Infrastructure/Options/SecurityOptions.cs`:

```csharp
public int LockoutMaxAttempts { get; set; } = 5;
public int LockoutDurationMinutes { get; set; } = 15;
public string DataProtectionPath { get; set; } = "./dataprotection-keys";
```
