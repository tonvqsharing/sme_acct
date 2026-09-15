namespace SmeAccounting.Modules.Authorization.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class AuthorizationModuleExtensions
{
    public static IServiceCollection AddAuthorizationModule(this IServiceCollection services)
    {
        new AuthorizationModule().AddModule(services);
        return services.AddPermissionPolicies();
    }
}
