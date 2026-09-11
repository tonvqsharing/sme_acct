namespace SmeAccounting.Modules.Organization.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class OrganizationModuleExtensions
{
    public static IServiceCollection AddOrganizationModule(this IServiceCollection services)
        => new OrganizationModule().AddModule(services);
}
