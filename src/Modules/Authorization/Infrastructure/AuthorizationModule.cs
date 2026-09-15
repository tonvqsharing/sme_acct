namespace SmeAccounting.Modules.Authorization.Infrastructure;

using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application;
using SmeAccounting.Modules.Authorization.Application;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.Modules.Authorization.Application.Authorization;
using SmeAccounting.Modules.Authorization.Infrastructure.Services;

public sealed class AuthorizationModule : IModule
{
    public IServiceCollection AddModule(IServiceCollection services) => services
        .AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<AuthorizationApplicationMarker>())
        .AddScoped<IRoleService, RoleService>()
        .AddScoped<IPermissionService, PermissionService>()
        .AddSingleton<IAuthorizationHandler, PermissionAuthorizationHandler>();
}
