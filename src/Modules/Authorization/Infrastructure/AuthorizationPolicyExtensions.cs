using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Modules.Authorization.Application.Authorization;
using SmeAccounting.Modules.Authorization.Domain;

namespace SmeAccounting.Modules.Authorization.Infrastructure;

public static class AuthorizationPolicyExtensions
{
    public static IServiceCollection AddPermissionPolicies(this IServiceCollection services)
    {
        services.AddAuthorization(options =>
        {
            foreach (var permission in Permissions.All)
            {
                var requirement = new PermissionRequirement(permission);
                options.AddPolicy($"Permission:{permission}", policy => policy.AddRequirements(requirement));
            }
        });

        return services;
    }
}
