namespace SmeAccounting.Infrastructure;

using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Infrastructure.Providers;
using SmeAccounting.SharedKernel;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services)
    {
        services.AddHttpContextAccessor();
        services.AddSingleton<IDateTimeProvider, SystemDateTimeProvider>();
        services.AddScoped<ICurrentUserProvider, HttpContextCurrentUserProvider>();

        return services;
    }
}