using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Infrastructure.Audit;

public static class AuditServiceExtensions
{
    public static IServiceCollection AddAuditInfrastructure(this IServiceCollection services)
    {
        services.AddScoped<IAuditLoggingService, AuditLoggingService>();
        return services;
    }
}
