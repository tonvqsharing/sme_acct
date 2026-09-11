namespace SmeAccounting.Modules.Organization.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.Organization.Application;

public sealed class OrganizationModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<OrganizationApplicationMarker>());
}
