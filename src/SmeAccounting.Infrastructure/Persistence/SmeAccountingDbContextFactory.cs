using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace SmeAccounting.Infrastructure.Persistence;

public class SmeAccountingDbContextFactory : IDesignTimeDbContextFactory<SmeAccountingDbContext>
{
    public SmeAccountingDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<SmeAccountingDbContext>();
        optionsBuilder.UseNpgsql("Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456");
        return new SmeAccountingDbContext(optionsBuilder.Options);
    }
}
