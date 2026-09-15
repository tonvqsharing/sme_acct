using Microsoft.AspNetCore.Authorization;
using SmeAccounting.Modules.Authorization.Domain;

namespace SmeAccounting.Modules.Authorization.Application.Authorization;

public sealed class PermissionAuthorizationHandler : AuthorizationHandler<PermissionRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        PermissionRequirement requirement)
    {
        var permissions = context.User.GetPermissions();

        if (permissions.Contains(requirement.Permission) ||
            permissions.Contains(Permissions.Users.ManageRoles))
        {
            context.Succeed(requirement);
        }

        return Task.CompletedTask;
    }
}
