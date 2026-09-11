namespace SmeAccounting.Modules.GeneralLedger.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.GeneralLedger.Application;

public sealed class GeneralLedgerModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<GeneralLedgerApplicationMarker>());
}
