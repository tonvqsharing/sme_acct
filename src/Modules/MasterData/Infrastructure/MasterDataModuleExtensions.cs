namespace SmeAccounting.Modules.MasterData.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class MasterDataModuleExtensions
{
    public static IServiceCollection AddMasterDataModule(this IServiceCollection services)
        => new MasterDataModule().AddModule(services);
}
