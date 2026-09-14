using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Infrastructure.ForwardedHeaders;

public static class ForwardedHeadersServiceExtensions
{
    public static IServiceCollection AddForwardedHeadersInfrastructure(this IServiceCollection services)
    {
        services.Configure<ForwardedHeadersOptions>(options =>
        {
            options.ForwardedHeaders =
                Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedFor |
                Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedProto;
            options.KnownProxies.Clear();
        });

        return services;
    }
}
