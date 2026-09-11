namespace SmeAccounting.Application;

using Microsoft.Extensions.DependencyInjection;

public interface IModule
{
    IServiceCollection AddModule(IServiceCollection services);
}