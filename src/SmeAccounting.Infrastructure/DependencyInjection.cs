using System.IO;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Infrastructure.Audit;
using SmeAccounting.Infrastructure.ForwardedHeaders;
using SmeAccounting.Infrastructure.Health;
using SmeAccounting.Infrastructure.Localization;
using SmeAccounting.Infrastructure.Logging;
using SmeAccounting.Infrastructure.Options;
using SmeAccounting.Infrastructure.Persistence;
using SmeAccounting.Infrastructure.Providers;
using SmeAccounting.Infrastructure.Storage;
using SmeAccounting.Infrastructure.Validation;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddHttpContextAccessor();

        // Persistence
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? "Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres";

        services.AddDbContext<SmeAccountingDbContext>(options =>
        {
            options.UseNpgsql(connectionString, npgsqlOptions =>
            {
                npgsqlOptions.EnableRetryOnFailure(3);
                npgsqlOptions.CommandTimeout(30);
            });
        });

        // Providers
        services.AddSingleton<IDateTimeProvider, SystemDateTimeProvider>();
        services.AddScoped<ICurrentUserProvider, HttpContextCurrentUserProvider>();

        // Logging
        services.AddSerilogInfrastructure(configuration);

        // Options
        services.AddInfrastructureOptions(configuration);

        // Validation
        services.AddValidationInfrastructure();

        // Localization
        services.AddLocalizationInfrastructure();

        // Forwarded Headers
        services.AddForwardedHeadersInfrastructure();

        // Health Checks
        services.AddHealthInfrastructure();

        // Audit
        services.AddAuditInfrastructure();

        // Storage
        services.AddFileStorage();

        // Security — Data Protection with persistent keys
        services.AddDataProtection()
            .PersistKeysToFileSystem(
                new DirectoryInfo(
                    configuration["Security:DataProtectionPath"] ?? "./dataprotection-keys"))
            .SetApplicationName("SmeAccounting");

        return services;
    }
}
