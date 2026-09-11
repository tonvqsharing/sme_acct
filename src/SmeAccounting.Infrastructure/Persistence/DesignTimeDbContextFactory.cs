using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace SmeAccounting.Infrastructure.Persistence;

public class DesignTimeDbContextFactory : IDesignTimeDbContextFactory<SmeAccountingDbContext>
{
    public SmeAccountingDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<SmeAccountingDbContext>();
        var connectionString = Environment.GetEnvironmentVariable("SME_ACCT_CONNECTION_STRING")
            ?? "Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres";

        optionsBuilder.UseNpgsql(connectionString, o => o.EnableRetryOnFailure());

        return new SmeAccountingDbContext(optionsBuilder.Options);
    }
}
