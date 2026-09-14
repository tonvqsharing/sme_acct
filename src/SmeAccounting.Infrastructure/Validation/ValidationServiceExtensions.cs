using System.Reflection;
using FluentValidation;
using Microsoft.Extensions.DependencyInjection;

namespace SmeAccounting.Infrastructure.Validation;

public static class ValidationServiceExtensions
{
    public static IServiceCollection AddValidationInfrastructure(this IServiceCollection services)
    {
        services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());
        return services;
    }
}
