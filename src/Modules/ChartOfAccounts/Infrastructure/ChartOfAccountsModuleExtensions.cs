namespace SmeAccounting.Modules.ChartOfAccounts.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class ChartOfAccountsModuleExtensions
{
    public static IServiceCollection AddChartOfAccountsModule(this IServiceCollection services)
        => new ChartOfAccountsModule().AddModule(services);
}
