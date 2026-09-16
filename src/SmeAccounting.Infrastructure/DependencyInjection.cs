using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Adapters;
using SmeAccounting.Infrastructure.Persistence;
using SmeAccounting.Infrastructure.Repositories;
using SmeAccounting.Infrastructure.Services;

namespace SmeAccounting.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        Action<DbContextOptionsBuilder>? configureOptions = null)
    {
        services.AddDbContext<SmeAccountingDbContext>((sp, options) =>
        {
            configureOptions?.Invoke(options);
        });

        services.AddScoped<IUnitOfWork>(sp =>
            sp.GetRequiredService<SmeAccountingDbContext>());

        services.AddScoped<IAccountRepository, EfAccountRepository>();
        services.AddScoped<IJournalEntryRepository, EfJournalEntryRepository>();

        services.AddSingleton<IClock, SystemClock>();
        services.AddScoped<IAuditLogger, AuditLogger>();
        services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>();

        return services;
    }
}
