using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
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
        IConfiguration configuration)
    {
        services.AddDbContext<SmeAccountingDbContext>((sp, options) =>
        {
            var connectionString = configuration.GetConnectionString("DefaultConnection")
                ?? "Host=localhost;Database=sme_accounting;Username=postgres;Password=postgres";
            options.UseNpgsql(connectionString);
        });

        services.AddScoped<IUnitOfWork>(sp =>
            sp.GetRequiredService<SmeAccountingDbContext>());

        services.AddScoped<IAccountRepository, EfAccountRepository>();
        services.AddScoped<IJournalEntryRepository, EfJournalEntryRepository>();
        services.AddScoped<ICompanyRepository, EfCompanyRepository>();
        services.AddScoped<ICurrencyRepository, EfCurrencyRepository>();
        services.AddScoped<IExchangeRateRepository, EfExchangeRateRepository>();
        services.AddScoped<IDepartmentRepository, EfDepartmentRepository>();
        services.AddScoped<ICostCenterRepository, EfCostCenterRepository>();
        services.AddScoped<IProjectRepository, EfProjectRepository>();
        services.AddScoped<IVoucherTypeRepository, EfVoucherTypeRepository>();
        services.AddScoped<IDocumentNumberingSeriesRepository, EfDocumentNumberingSeriesRepository>();
        services.AddScoped<ITransactionReasonRepository, EfTransactionReasonRepository>();

        services.AddSingleton<IClock, SystemClock>();
        services.AddScoped<IAuditLogger, AuditLogger>();
        services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>();

        return services;
    }
}
