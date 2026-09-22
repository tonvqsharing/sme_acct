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
        services.AddScoped<IPostingConfigurationRepository, EfPostingConfigurationRepository>();
        services.AddScoped<IOpeningBalanceMappingRepository, EfOpeningBalanceMappingRepository>();
        services.AddScoped<IOpeningBalancePeriodRepository, EfOpeningBalancePeriodRepository>();
        services.AddScoped<IOpeningBalanceEntryRepository, EfOpeningBalanceEntryRepository>();
        services.AddScoped<ITaxTypeRepository, EfTaxTypeRepository>();
        services.AddScoped<ITaxTreatmentRepository, EfTaxTreatmentRepository>();
        services.AddScoped<ITaxAuthorityRepository, EfTaxAuthorityRepository>();
        services.AddScoped<ITaxRateRepository, EfTaxRateRepository>();
        services.AddScoped<ITaxRuleRepository, EfTaxRuleRepository>();
        services.AddScoped<ITaxExemptionReasonRepository, EfTaxExemptionReasonRepository>();
        services.AddScoped<ITaxAccountingMappingRepository, EfTaxAccountingMappingRepository>();
        services.AddScoped<ITaxPeriodRepository, EfTaxPeriodRepository>();
        services.AddScoped<ICustomerRepository, EfCustomerRepository>();
        services.AddScoped<ISupplierRepository, EfSupplierRepository>();
        services.AddScoped<IEmployeeRepository, EfEmployeeRepository>();
        services.AddScoped<IPaymentTermRepository, EfPaymentTermRepository>();
        services.AddScoped<IUomRepository, EfUomRepository>();
        services.AddScoped<IItemCategoryRepository, EfItemCategoryRepository>();
        services.AddScoped<IWarehouseRepository, EfWarehouseRepository>();
        services.AddScoped<IUomConversionRepository, EfUomConversionRepository>();
        services.AddScoped<IItemRepository, EfItemRepository>();
        services.AddScoped<IServiceItemRepository, EfServiceItemRepository>();
        services.AddScoped<IInventoryValuationPolicyRepository, EfInventoryValuationPolicyRepository>();
        services.AddScoped<IInventoryAdjustmentReasonRepository, EfInventoryAdjustmentReasonRepository>();
        services.AddScoped<IInventoryAccountingConfigurationRepository, EfInventoryAccountingConfigurationRepository>();
        services.AddScoped<ICompanySettingRepository, EfCompanySettingRepository>();
        services.AddScoped<IBankRepository, EfBankRepository>();
        services.AddScoped<IBankBranchRepository, EfBankBranchRepository>();
        services.AddScoped<IBankAccountRepository, EfBankAccountRepository>();
        services.AddScoped<IUsersRepository, EfUsersRepository>();
        services.AddScoped<IRoleRepository, EfRoleRepository>();
        services.AddScoped<IUserRoleRepository, EfUserRoleRepository>();
        services.AddScoped<ICompanyMembershipRepository, EfCompanyMembershipRepository>();

        services.AddSingleton<IClock, SystemClock>();
        services.AddScoped<IAuditLogger, AuditLogger>();
        services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>();
        services.AddScoped<IMicrosoftSignInProvider, MicrosoftSignInProvider>();

        return services;
    }
}
