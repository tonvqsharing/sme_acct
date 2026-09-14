using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Microsoft.Extensions.Configuration;

namespace SmeAccounting.Infrastructure.Persistence;

public class DesignTimeDbContextFactory : IDesignTimeDbContextFactory<SmeAccountingDbContext>
{
    public SmeAccountingDbContext CreateDbContext(string[] args)
    {
        var configuration = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .Build();

        var provider = DbProviderSelector.Resolve(configuration);
        var connectionString = DbProviderSelector.ResolveConnectionString(configuration, provider);

        var optionsBuilder = new DbContextOptionsBuilder<SmeAccountingDbContext>();
        DbProviderSelector.Configure(optionsBuilder, provider, connectionString, 3, 30);
        return new SmeAccountingDbContext(optionsBuilder.Options);
    }
}
