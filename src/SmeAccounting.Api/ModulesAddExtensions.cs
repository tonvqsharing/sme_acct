namespace SmeAccounting.Api;

using SmeAccounting.Application;

public static class ModulesAddExtensions
{
    public static IServiceCollection AddModules(this IServiceCollection services, IEnumerable<IModule> modules)
    {
        foreach (var module in modules)
        {
            module.AddModule(services);
        }

        return services;
    }
}