using Microsoft.AspNetCore.Identity;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.Modules.Identity.Infrastructure;

namespace SmeAccounting.Modules.Authorization.Infrastructure.Services;

public sealed class PermissionService : IPermissionService
{
    public const string PermissionClaimType = "permission";

    private readonly RoleManager<ApplicationRole> _roles;
    private readonly UserManager<ApplicationUser> _users;

    public PermissionService(RoleManager<ApplicationRole> roles, UserManager<ApplicationUser> users)
    {
        _roles = roles;
        _users = users;
    }

    public async Task<IReadOnlyList<string>> GetPermissionsAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var user = await _users.FindByIdAsync(userId.ToString()).ConfigureAwait(false);
        if (user is null)
        {
            return [];
        }

        var permissions = new HashSet<string>(StringComparer.Ordinal);
        var roleNames = await _users.GetRolesAsync(user).ConfigureAwait(false);
        foreach (var roleName in roleNames)
        {
            var role = await _roles.FindByNameAsync(roleName).ConfigureAwait(false);
            if (role is null)
            {
                continue;
            }

            var claims = await _roles.GetClaimsAsync(role).ConfigureAwait(false);
            foreach (var claim in claims)
            {
                if (claim.Type == PermissionClaimType)
                {
                    permissions.Add(claim.Value);
                }
            }
        }

        return permissions.ToList();
    }

    public async Task<bool> HasPermissionAsync(Guid userId, string permission, CancellationToken cancellationToken = default)
    {
        var permissions = await GetPermissionsAsync(userId, cancellationToken).ConfigureAwait(false);
        return permissions.Contains(permission, StringComparer.Ordinal);
    }
}
