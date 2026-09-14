using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Logging;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public static class RoleSeeder
{
    public static readonly (string Name, string Description, IReadOnlyList<string> Permissions)[] StandardRoles =
    [
        ("Admin", "System administrator with full access",
            [.. SmeAccounting.Modules.Identity.Application.Permissions.All]),
        ("ChiefAccountant", "Head of accounting department",
            [.. SmeAccounting.Modules.Identity.Application.Permissions.Accounts.All, .. SmeAccounting.Modules.Identity.Application.Permissions.Journal.All, .. SmeAccounting.Modules.Identity.Application.Permissions.Reports.All, .. SmeAccounting.Modules.Identity.Application.Permissions.Settings.All]),
        ("Accountant", "Regular accountant user",
            [SmeAccounting.Modules.Identity.Application.Permissions.Accounts.View, SmeAccounting.Modules.Identity.Application.Permissions.Accounts.Create, SmeAccounting.Modules.Identity.Application.Permissions.Accounts.Edit,
             SmeAccounting.Modules.Identity.Application.Permissions.Journal.View, SmeAccounting.Modules.Identity.Application.Permissions.Journal.Create, SmeAccounting.Modules.Identity.Application.Permissions.Journal.Edit,
             SmeAccounting.Modules.Identity.Application.Permissions.Reports.View]),
        ("Viewer", "Read-only access",
            [SmeAccounting.Modules.Identity.Application.Permissions.Accounts.View, SmeAccounting.Modules.Identity.Application.Permissions.Journal.View, SmeAccounting.Modules.Identity.Application.Permissions.Reports.View, SmeAccounting.Modules.Identity.Application.Permissions.Audit.View]),
        ("Auditor", "Audit and compliance review access",
            [SmeAccounting.Modules.Identity.Application.Permissions.Audit.View, SmeAccounting.Modules.Identity.Application.Permissions.Accounts.View, SmeAccounting.Modules.Identity.Application.Permissions.Journal.View, SmeAccounting.Modules.Identity.Application.Permissions.Reports.View, SmeAccounting.Modules.Identity.Application.Permissions.Reports.Export])
    ];

    public static async Task SeedAsync(RoleManager<ApplicationRole> roleManager, ILogger logger)
    {
        foreach (var (name, description, permissions) in StandardRoles)
        {
            var role = await roleManager.FindByNameAsync(name);
            if (role == null)
            {
                role = new ApplicationRole
                {
                    Name = name,
                    NormalizedName = name.ToUpperInvariant(),
                    Description = description,
                    DisplayOrder = Array.FindIndex(StandardRoles, r => r.Name == name)
                };

                var result = await roleManager.CreateAsync(role);
                if (result.Succeeded)
                {
                    logger.LogInformation("Created role {RoleName}", name);

                    foreach (var permission in permissions)
                    {
                        await roleManager.AddClaimAsync(role,
                            new System.Security.Claims.Claim("permission", permission));
                    }
                }
                else
                {
                    logger.LogError("Failed to create role {RoleName}: {Errors}",
                        name, string.Join(", ", result.Errors.Select(e => e.Description)));
                }
            }
        }
    }
}
