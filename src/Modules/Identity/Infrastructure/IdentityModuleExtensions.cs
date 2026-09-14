namespace SmeAccounting.Modules.Identity.Infrastructure;

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

public static class IdentityModuleExtensions
{
    public static IServiceCollection AddIdentityModule(this IServiceCollection services, IConfiguration configuration)
    {
        new IdentityModule().AddModule(services);
        services.AddIdentityInfrastructure(configuration);
        return services;
    }
}
