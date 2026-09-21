using Microsoft.EntityFrameworkCore; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports; using SmeAccounting.Infrastructure.Persistence;
namespace SmeAccounting.Infrastructure.Repositories;
public class EfInventoryAccountingConfigurationRepository : IInventoryAccountingConfigurationRepository
{
    private readonly SmeAccountingDbContext _ctx;
    public EfInventoryAccountingConfigurationRepository(SmeAccountingDbContext ctx) => _ctx = ctx;
    public Task<InventoryAccountingConfiguration?> GetByCompanyAsync(long companyId) => _ctx.InventoryAccountingConfigurations.FirstOrDefaultAsync(e => e.CompanyId == companyId);
    public Task<InventoryAccountingConfiguration?> GetByIdAsync(long id) => _ctx.InventoryAccountingConfigurations.FirstOrDefaultAsync(e => e.Id == id);
    public Task AddAsync(InventoryAccountingConfiguration configuration) => _ctx.InventoryAccountingConfigurations.AddAsync(configuration).AsTask();
}
