namespace SmeAccounting.Modules.GeneralLedger.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class GeneralLedgerModuleExtensions
{
    public static IServiceCollection AddGeneralLedgerModule(this IServiceCollection services)
        => new GeneralLedgerModule().AddModule(services);
}
