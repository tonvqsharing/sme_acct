namespace SmeAccounting.Modules.FinancialReporting.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class FinancialReportingModuleExtensions
{
    public static IServiceCollection AddFinancialReportingModule(this IServiceCollection services)
        => new FinancialReportingModule().AddModule(services);
}
