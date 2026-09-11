namespace SmeAccounting.Modules.AccountingPeriod.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class AccountingPeriodModuleExtensions
{
    public static IServiceCollection AddAccountingPeriodModule(this IServiceCollection services)
        => new AccountingPeriodModule().AddModule(services);
}
