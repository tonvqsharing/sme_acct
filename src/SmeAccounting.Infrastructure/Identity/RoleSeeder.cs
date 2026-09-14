using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Logging;

namespace SmeAccounting.Infrastructure.Identity;

public static class RoleSeeder
{
    public static readonly (string Name, string Description, IReadOnlyList<string> Permissions)[] StandardRoles =
    [
        ("Admin", "System administrator with full access",
            [.. Permissions.All]),
        ("ChiefAccountant", "Head of accounting department",
            [.. Permissions.Accounts.All, .. Permissions.Journal.All, .. Permissions.Reports.All, .. Permissions.Settings.All]),
        ("Accountant", "Regular accountant user",
            [Permissions.Accounts.View, Permissions.Accounts.Create, Permissions.Accounts.Edit,
             Permissions.Journal.View, Permissions.Journal.Create, Permissions.Journal.Edit,
             Permissions.Reports.View]),
        ("Viewer", "Read-only access",
            [Permissions.Accounts.View, Permissions.Journal.View, Permissions.Reports.View, Permissions.Audit.View]),
        ("Auditor", "Audit and compliance review access",
            [Permissions.Audit.View, Permissions.Accounts.View, Permissions.Journal.View, Permissions.Reports.View, Permissions.Reports.Export])
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
