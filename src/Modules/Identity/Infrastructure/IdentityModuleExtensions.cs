namespace SmeAccounting.Modules.Identity.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class IdentityModuleExtensions
{
    public static IServiceCollection AddIdentityModule(this IServiceCollection services)
        => new IdentityModule().AddModule(services);
}
