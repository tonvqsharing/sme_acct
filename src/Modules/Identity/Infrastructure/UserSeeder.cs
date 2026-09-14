using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Logging;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public static class UserSeeder
{
    public static async Task SeedAsync(
        UserManager<ApplicationUser> userManager,
        RoleManager<ApplicationRole> roleManager,
        ILogger logger,
        string? adminPassword = null)
    {
        var email = "admin@smeaccounting.vn";
        var user = await userManager.FindByEmailAsync(email);

        if (user == null)
        {
            user = new ApplicationUser
            {
                UserName = "admin",
                Email = email,
                EmailConfirmed = true,
                DisplayName = "System Administrator",
                IsEnabled = true,
                CreatedAtUtc = DateTime.UtcNow
            };

            var password = adminPassword ?? Environment.GetEnvironmentVariable("ADMIN_PASSWORD") ?? "Admin@12345";
            var result = await userManager.CreateAsync(user, password);

            if (result.Succeeded)
            {
                await userManager.AddToRoleAsync(user, "Admin");
                logger.LogInformation("Default admin user created");
            }
            else
            {
                logger.LogError("Failed to create admin user: {Errors}",
                    string.Join(", ", result.Errors.Select(e => e.Description)));
            }
        }
    }
}
