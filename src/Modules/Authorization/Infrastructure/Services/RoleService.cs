using System.Security.Claims;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.Modules.Authorization.Domain;
using SmeAccounting.Modules.Identity.Infrastructure;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Infrastructure.Services;

public sealed class RoleService : IRoleService
{
    public const string PermissionClaimType = "permission";

    private readonly RoleManager<ApplicationRole> _roles;
    private readonly UserManager<ApplicationUser> _users;

    public RoleService(RoleManager<ApplicationRole> roles, UserManager<ApplicationUser> users)
    {
        _roles = roles;
        _users = users;
    }

    public async Task<Result> CreateAsync(string roleName, string? description, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (await _roles.FindByNameAsync(roleName).ConfigureAwait(false) is not null)
        {
            return Result.Fail("Authorization.RoleAlreadyExists", $"Role '{roleName}' already exists.");
        }

        var role = new ApplicationRole
        {
            Name = roleName,
            NormalizedName = roleName.ToUpperInvariant(),
            Description = description ?? string.Empty,
            DisplayOrder = 0,
        };

        var created = await _roles.CreateAsync(role).ConfigureAwait(false);
        if (!created.Succeeded)
        {
            return IdentityFailure("Authorization.RoleCreateFailed", created.Errors);
        }

        return Result.Success();
    }

    public async Task<Result> DeleteAsync(string roleName, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var deleted = await _roles.DeleteAsync(role).ConfigureAwait(false);
        if (!deleted.Succeeded)
        {
            return IdentityFailure("Authorization.RoleDeleteFailed", deleted.Errors);
        }

        return Result.Success();
    }

    public async Task<Result> AssignPermissionAsync(string roleName, string permission, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!Permissions.All.Contains(permission))
        {
            return Result.Fail("Authorization.UnknownPermission", $"Permission '{permission}' is not a known permission.");
        }

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var claims = await _roles.GetClaimsAsync(role).ConfigureAwait(false);
        if (claims.Any(c => c.Type == PermissionClaimType && c.Value == permission))
        {
            return Result.Success();
        }

        var added = await _roles.AddClaimAsync(role, new Claim(PermissionClaimType, permission)).ConfigureAwait(false);
        if (!added.Succeeded)
        {
            return IdentityFailure("Authorization.PermissionAssignFailed", added.Errors);
        }

        return Result.Success();
    }

    public async Task<Result> RevokePermissionAsync(string roleName, string permission, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!Permissions.All.Contains(permission))
        {
            return Result.Fail("Authorization.UnknownPermission", $"Permission '{permission}' is not a known permission.");
        }

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var claims = await _roles.GetClaimsAsync(role).ConfigureAwait(false);
        foreach (var claim in claims.Where(c => c.Type == PermissionClaimType && c.Value == permission).ToList())
        {
            var removed = await _roles.RemoveClaimAsync(role, claim).ConfigureAwait(false);
            if (!removed.Succeeded)
            {
                return IdentityFailure("Authorization.PermissionRevokeFailed", removed.Errors);
            }
        }

        return Result.Success();
    }

    public async Task<Result> AssignRoleToUserAsync(Guid userId, string roleName, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var user = await _users.FindByIdAsync(userId.ToString()).ConfigureAwait(false);
        if (user is null)
        {
            return Result.Fail("Authorization.UserNotFound", $"User '{userId}' was not found.");
        }

        if (await _users.IsInRoleAsync(user, roleName).ConfigureAwait(false))
        {
            return Result.Success();
        }

        var added = await _users.AddToRoleAsync(user, roleName).ConfigureAwait(false);
        if (!added.Succeeded)
        {
            return IdentityFailure("Authorization.RoleAssignmentFailed", added.Errors);
        }

        return Result.Success();
    }

    public async Task<Result> RemoveRoleFromUserAsync(Guid userId, string roleName, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var user = await _users.FindByIdAsync(userId.ToString()).ConfigureAwait(false);
        if (user is null)
        {
            return Result.Fail("Authorization.UserNotFound", $"User '{userId}' was not found.");
        }

        if (!await _users.IsInRoleAsync(user, roleName).ConfigureAwait(false))
        {
            return Result.Success();
        }

        var removed = await _users.RemoveFromRoleAsync(user, roleName).ConfigureAwait(false);
        if (!removed.Succeeded)
        {
            return IdentityFailure("Authorization.RoleAssignmentFailed", removed.Errors);
        }

        return Result.Success();
    }

    public async Task<Result<IReadOnlyList<string>>> GetRolePermissionsAsync(string roleName, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
        if (role is null)
        {
            return Result<IReadOnlyList<string>>.Fail("Authorization.RoleNotFound", $"Role '{roleName}' was not found.");
        }

        var claims = await _roles.GetClaimsAsync(role).ConfigureAwait(false);
        IReadOnlyList<string> permissions = claims
            .Where(c => c.Type == PermissionClaimType)
            .Select(c => c.Value)
            .ToList();

        return Result<IReadOnlyList<string>>.Create(permissions);
    }

    public async Task<Result<IReadOnlyList<string>>> ListRolesAsync(CancellationToken cancellationToken = default)
    {
        var names = await _roles.Roles
            .Select(r => r.Name)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        List<string> result = [];
        foreach (var name in names)
        {
            if (name is not null)
            {
                result.Add(name);
            }
        }

        return Result<IReadOnlyList<string>>.Create(result);
    }

    private static Result IdentityFailure(string code, IEnumerable<IdentityError> errors)
    {
        return Result.Fail(code, string.Join("; ", errors.Select(e => e.Description)));
    }
}
