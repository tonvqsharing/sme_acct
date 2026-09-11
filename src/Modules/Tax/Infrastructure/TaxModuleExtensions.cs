namespace SmeAccounting.Modules.Tax.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class TaxModuleExtensions
{
    public static IServiceCollection AddTaxModule(this IServiceCollection services)
        => new TaxModule().AddModule(services);
}
