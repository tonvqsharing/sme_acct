# G1 CompanyMembership/User/Role Domain Verification

Date: 2026-09-21
Loop: loop-stack/01-system-security

## Verification Summary

All domain entities follow BaseEntity pattern with private parameterless ctor for EF Core and public validating ctor using DomainException.

### Entities Verified

**User** `src/SmeAccounting.Domain/Entities/User.cs`
- Global user, no CompanyId
- Properties: ExternalId, Email, DisplayName, UserName?, IsActive
- Validation: ExternalId/Email/DisplayName required, Email lowercased, ExternalId trimmed
- Domain event: UserCreated(UserId, OccurredOn) - minimal, no CompanyId
- BaseEntity pattern: private ctor, public ctor, AddDomainEvent

**Role** `src/SmeAccounting.Domain/Entities/Role.cs`
- Company-scoped
- Properties: CompanyId, Code, Name, Description?, IsActive
- Validation: CompanyId>0, Code/Name required
- Domain event: RoleCreated(RoleId, CompanyId, OccurredOn)
- BaseEntity pattern confirmed

**CompanyMembership** `src/SmeAccounting.Domain/Entities/CompanyMembership.cs`
- Linking aggregate UserId + CompanyId
- Properties: UserId, CompanyId, IsActive, JoinedAt
- Validation: ids >0
- Domain event: CompanyMembershipCreated(MembershipId, CompanyId, OccurredOn)
- BaseEntity pattern confirmed

**UserRole** `src/SmeAccounting.Domain/Entities/UserRole.cs`
- Per-company role assignment
- Properties: UserId, RoleId, CompanyId, IsActive
- Validation: ids >0
- Domain event: UserRoleAssigned(UserRoleId, CompanyId, OccurredOn)
- BaseEntity pattern confirmed

## Domain Events Minimalism

All events extend DomainEvent with OccurredOn + EventId.
Payload is minimal:
- UserCreated: UserId only
- RoleCreated: RoleId + CompanyId
- CompanyMembershipCreated: MembershipId + CompanyId
- UserRoleAssigned: UserRoleId + CompanyId

No entity data duplication in events.

## Ports

- IUsersRepository: GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllAsync, AddAsync
- IRoleRepository: GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync, AddAsync
- ICompanyMembershipRepository: AddAsync
- IUserRoleRepository: AddAsync

All ports in Domain/Ports, zero NuGet refs.

## EF Configurations

Snake_case table names, xmin row version, FK Restrict, unique indexes.

**UserConfiguration** `users`
- Columns: id, external_id, email, display_name, user_name, is_active, xmin
- Unique indexes: external_id, email
- No CompanyId

**RoleConfiguration** `roles`
- Columns: id, company_id, code, name, description, is_active, xmin
- Unique index: (company_id, code)
- FK: CompanyId DeleteBehavior.Restrict

**CompanyMembershipConfiguration** `company_memberships`
- Columns: id, user_id, company_id, is_active, joined_at, xmin
- Unique index: (user_id, company_id)
- FK Restrict to Company and User

**UserRoleConfiguration** `user_roles`
- Columns: id, user_id, role_id, company_id, is_active, xmin
- Unique index: (user_id, role_id, company_id)
- FK Restrict to Company, User, Role

## Repositories

EfUsersRepository, EfRoleRepository, EfCompanyMembershipRepository, EfUserRoleRepository implemented in Infrastructure/Repositories.
Reads use AsNoTracking where appropriate, writes via AddAsync.

## DbContext

SmeAccountingDbContext includes DbSet<User> Users, DbSet<Role> Roles, DbSet<CompanyMembership> CompanyMemberships, DbSet<UserRole> UserRoles.
Domain events ignored in OnModelCreating.

## Constraints Satisfied

- User global with ExternalId mandatory, Email globally unique
- Role company-scoped
- CompanyMembership unique per user/company
- UserRole unique per user/role/company
- BaseEntity pattern
- DomainException validation
- Domain events minimalism
- EF configs snake_case/xmin/FK Restrict
- Clean Architecture 22 NetArchTest rules pass
- Domain zero NuGet refs

## Discoveries Appended

Discoveries appended to loop-stack/01-system-security/MEMORY.md under 2026-09-21 G1 CompanyMembership/User/Role design verification.
STATUS.md updated: Task completed, progress 2/7.
