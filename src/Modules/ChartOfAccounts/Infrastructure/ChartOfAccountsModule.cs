namespace SmeAccounting.Modules.ChartOfAccounts.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.ChartOfAccounts.Application;

public sealed class ChartOfAccountsModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<ChartOfAccountsApplicationMarker>());
}
