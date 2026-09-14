using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Microsoft.Extensions.Configuration;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public class IdentityDbContextFactory : IDesignTimeDbContextFactory<IdentityDbContext>
{
    public IdentityDbContext CreateDbContext(string[] args)
    {
        var configuration = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .Build();

        var provider = DbProviderSelector.Resolve(configuration);
        var connectionString = DbProviderSelector.ResolveConnectionString(configuration, provider);

        var optionsBuilder = new DbContextOptionsBuilder<IdentityDbContext>();
        DbProviderSelector.Configure(optionsBuilder, provider, connectionString, 3, 30);
        return new IdentityDbContext(optionsBuilder.Options);
    }
}
