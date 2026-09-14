namespace SmeAccounting.Modules.Identity.Infrastructure;

using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.Identity.Application;

public sealed class IdentityModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services)
    {
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<IdentityApplicationMarker>());

        return services;
    }
}
