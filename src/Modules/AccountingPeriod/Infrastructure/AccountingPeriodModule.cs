namespace SmeAccounting.Modules.AccountingPeriod.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.AccountingPeriod.Application;

public sealed class AccountingPeriodModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<AccountingPeriodApplicationMarker>());
}
