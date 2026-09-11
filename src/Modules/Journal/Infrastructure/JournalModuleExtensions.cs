namespace SmeAccounting.Modules.Journal.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class JournalModuleExtensions
{
    public static IServiceCollection AddJournalModule(this IServiceCollection services)
        => new JournalModule().AddModule(services);
}
