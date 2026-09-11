namespace SmeAccounting.Modules.MasterData.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.MasterData.Application;

public sealed class MasterDataModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<MasterDataApplicationMarker>());
}
