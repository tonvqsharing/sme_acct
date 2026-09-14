using Microsoft.AspNetCore.Authorization;

namespace SmeAccounting.Modules.Identity.Application;

public class PermissionRequirement : IAuthorizationRequirement
{
    public string Permission { get; }

    public PermissionRequirement(string permission)
    {
        Permission = permission;
    }
}

public class PermissionAuthorizationHandler : AuthorizationHandler<PermissionRequirement>
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
