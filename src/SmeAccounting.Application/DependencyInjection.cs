namespace SmeAccounting.Application;

using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application.Behaviours;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services) => services
        .AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssemblyContaining<ApplicationMarker>();
            cfg.Lifetime = ServiceLifetime.Scoped;
        })
        .AddValidatorsFromAssembly(typeof(ApplicationMarker).Assembly, ServiceLifetime.Scoped)
        .AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehaviour<,>));
}