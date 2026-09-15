namespace SmeAccounting.Infrastructure.Persistence;

using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

public static class DbProviderSelector
{
    public static DatabaseProvider Resolve(IConfiguration configuration)
    {
        var raw = configuration["Database:Provider"];
        return Enum.TryParse<DatabaseProvider>(raw, ignoreCase: true, out var p)
            ? p
            : DatabaseProvider.PostgreSql;
    }

    public static string ResolveConnectionString(IConfiguration configuration, DatabaseProvider provider)
    {
        var explicitCs =
            configuration["Database:ConnectionString"]
            ?? configuration["SME_ACCT_CONNECTION_STRING"]
            ?? Environment.GetEnvironmentVariable("SME_ACCT_CONNECTION_STRING");

        if (!string.IsNullOrWhiteSpace(explicitCs)) return explicitCs;

        return provider switch
        {
            DatabaseProvider.PostgreSql =>
                configuration.GetConnectionString("DefaultConnection")
                ?? "Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres",
            DatabaseProvider.MariaDb =>
                "Server=localhost;Port=3306;Database=smeaccounting;User=root;Password=root",
            DatabaseProvider.Sqlite =>
                "Data Source=smeaccounting.db",
            DatabaseProvider.SqlServer =>
                "Server=localhost;Database=smeaccounting;User Id=sa;Password=Your_password123;TrustServerCertificate=True",
            _ => throw new InvalidOperationException($"Unsupported provider: {provider}")
        };
    }

    public static void Configure(
        DbContextOptionsBuilder options,
        DatabaseProvider provider,
        string connectionString,
        int retry,
        int timeout)
    {
        switch (provider)
        {
            case DatabaseProvider.PostgreSql:
                options.UseNpgsql(connectionString, o =>
                {
                    o.EnableRetryOnFailure(retry);
                    o.CommandTimeout(timeout);
                    o.MigrationsAssembly(typeof(DbProviderSelector).Assembly.GetName().Name);
                });
                break;

            case DatabaseProvider.MariaDb:
                options.UseMySql(
                    connectionString,
                    ServerVersion.AutoDetect(connectionString),
                    o =>
                    {
                        o.EnableRetryOnFailure(retry);
                        o.CommandTimeout(timeout);
                        o.MigrationsAssembly(typeof(DbProviderSelector).Assembly.GetName().Name);
                    });
                break;

            case DatabaseProvider.Sqlite:
                options.UseSqlite(connectionString, o =>
                {
                    o.CommandTimeout(timeout);
                    o.MigrationsAssembly(typeof(DbProviderSelector).Assembly.GetName().Name);
                });
                break;

            case DatabaseProvider.SqlServer:
                options.UseSqlServer(connectionString, o =>
                {
                    o.EnableRetryOnFailure(retry);
                    o.CommandTimeout(timeout);
                    o.MigrationsAssembly(typeof(DbProviderSelector).Assembly.GetName().Name);
                });
                break;

            default:
                throw new InvalidOperationException($"Unsupported provider: {provider}");
        }
    }
}
