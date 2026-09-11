namespace SmeAccounting.Modules.Audit.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class AuditModuleExtensions
{
    public static IServiceCollection AddAuditModule(this IServiceCollection services)
        => new AuditModule().AddModule(services);
}
