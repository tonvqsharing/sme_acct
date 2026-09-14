using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Infrastructure.Storage;

public static class StorageServiceExtensions
{
    public static IServiceCollection AddFileStorage(this IServiceCollection services)
    {
        services.AddScoped<IFileStorage, LocalFileStorage>();
        return services;
    }
}
