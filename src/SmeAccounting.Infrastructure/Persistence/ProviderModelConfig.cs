namespace SmeAccounting.Infrastructure.Persistence;

using Microsoft.EntityFrameworkCore;

public static class ProviderModelConfig
{
    public static void ApplyProviderSpecificConventions(ModelBuilder modelBuilder)
    {
        var providerName = modelBuilder.Model.FindAnnotation("Relational:ProviderName")?.Value as string ?? "";

        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            if (entityType.ClrType.Name.EndsWith("Entity", StringComparison.Ordinal) || entityType.ClrType.FullName?.Contains("BaseEntity") == true)
            {
                // Identity generation handled in DbContext
            }
        }

        // Provider-specific tweaks can be added here
        if (providerName.Contains("MySql") || providerName.Contains("MariaDb"))
        {
            // MariaDB: ensure string columns are not too long
        }
        else if (providerName.Contains("Sqlite"))
        {
            // SQLite: no additional tweaks needed
        }
        else if (providerName.Contains("SqlServer"))
        {
            // SQL Server: decimal precision already set
        }
    }
}
