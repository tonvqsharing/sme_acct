using System.Security.Claims;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Logging;
using SmeAccounting.Modules.Authorization.Domain;
using SmeAccounting.Modules.Identity.Infrastructure;

namespace SmeAccounting.Modules.Authorization.Infrastructure.Seeding;

public static class AuthorizationRoleSeeder
{
    public const string PermissionClaimType = "permission";

    private const string AdminEmail = "admin@smeaccounting.vn";

    public static async Task SeedAsync(
        RoleManager<ApplicationRole> roleManager,
        UserManager<ApplicationUser> userManager,
        ILogger logger)
    {
        for (var i = 0; i < Roles.All.Count; i++)
        {
            var roleName = Roles.All[i];
            var role = await roleManager.FindByNameAsync(roleName);
            if (role == null)
            {
                role = new ApplicationRole
                {
                    Name = roleName,
                    NormalizedName = roleName.ToUpperInvariant(),
                    Description = roleName,
                    DisplayOrder = i
                };

                var created = await roleManager.CreateAsync(role);
                if (!created.Succeeded)
                {
                    logger.LogError("Failed to create role {RoleName}: {Errors}",
                        roleName, string.Join(", ", created.Errors.Select(e => e.Description)));
                    continue;
                }

                logger.LogInformation("Created role {RoleName}", roleName);
            }

            var existingClaims = await roleManager.GetClaimsAsync(role);
            var existingPermissions = new HashSet<string>(
                existingClaims
                    .Where(c => c.Type == PermissionClaimType)
                    .Select(c => c.Value),
                StringComparer.Ordinal);

            foreach (var permission in RolePermissionMap.GetPermissions(roleName))
            {
                if (existingPermissions.Contains(permission))
                {
                    continue;
                }

                var added = await roleManager.AddClaimAsync(role, new Claim(PermissionClaimType, permission));
                if (added.Succeeded)
                {
                    logger.LogInformation("Added permission {Permission} to role {RoleName}", permission, roleName);
                }
                else
                {
                    logger.LogError("Failed to add permission {Permission} to role {RoleName}: {Errors}",
                        permission, roleName, string.Join(", ", added.Errors.Select(e => e.Description)));
                }
            }
        }

        var admin = await userManager.FindByEmailAsync(AdminEmail);
        if (admin != null && !await userManager.IsInRoleAsync(admin, Roles.Admin))
        {
            var assigned = await userManager.AddToRoleAsync(admin, Roles.Admin);
            if (assigned.Succeeded)
            {
                logger.LogInformation("Assigned role {RoleName} to {Email}", Roles.Admin, AdminEmail);
            }
            else
            {
                logger.LogError("Failed to assign role {RoleName} to {Email}: {Errors}",
                    Roles.Admin, AdminEmail, string.Join(", ", assigned.Errors.Select(e => e.Description)));
            }
        }
    }
}
