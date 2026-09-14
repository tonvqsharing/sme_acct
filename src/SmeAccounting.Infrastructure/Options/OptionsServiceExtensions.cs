using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Infrastructure.Options;

public static class OptionsServiceExtensions
{
    public static IServiceCollection AddInfrastructureOptions(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.Configure<ConnectionStringsOptions>(
            configuration.GetSection(ConnectionStringsOptions.SectionName));
        services.Configure<SerilogOptions>(
            configuration.GetSection(SerilogOptions.SectionName));
        services.Configure<SecurityOptions>(
            configuration.GetSection(SecurityOptions.SectionName));
        
        return services;
    }
}
