# System / Security Foundation Review — 2026-09-21

## Scope
Company, CompanySetting, CompanyMembership, User, UserRole, Role, DocumentNumberingSeries, VoucherType, TransactionReason with Microsoft-first Identity integration.

## Findings

### Architecture
- Clean Architecture 22 NetArchTest rules pass.
- Domain zero NuGet refs, Api has no Domain entity refs.

### Domain validation
- Entities use `DomainException` constructors, private parameterless ctor for EF, domain events minimalism.
- No domain unit tests. Invariants untested.

### Repository integration
- EF configs: snake_case, xmin row version, FK Restrict to Company, composite unique indexes per company.
- No integration tests.

### Concurrency safety — DocumentNumberingSeries
- `Increment()` exists but not used in Application layer.
- Optimistic concurrency via xmin only.
- No SELECT FOR UPDATE / retry policy. Risk of duplicate numbers under concurrent voucher creation.

### Identity / Security
- `IdentityUserAdapter` mapping fixed.
- `MicrosoftSignInProvider` is stub; no OpenID Connect / JWT wired.
- `AddAuthentication("PlaceholderScheme")` in Api.
- No `[Authorize]` attributes on controllers.
- DB connection string with password in appsettings.json.
- No secrets management.
- No audit logging tests.

## Recommendations
1. Add domain unit tests for all system security entities.
2. Add integration tests for repositories, uniqueness constraints, FK Restrict.
3. Implement atomic number generation for DocumentNumberingSeries: EF optimistic concurrency with retry or SELECT FOR UPDATE via Npgsql.
4. Wire Microsoft.Identity.Web for Entra ID, replace placeholder scheme.
5. Move connection string to environment variables / secrets.
6. Add authorization policies per company.
7. Add audit logging for Company, CompanyMembership, Role changes.
