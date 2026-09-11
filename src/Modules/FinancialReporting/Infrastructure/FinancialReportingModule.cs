namespace SmeAccounting.Modules.FinancialReporting.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.FinancialReporting.Application;

public sealed class FinancialReportingModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<FinancialReportingApplicationMarker>());
}
