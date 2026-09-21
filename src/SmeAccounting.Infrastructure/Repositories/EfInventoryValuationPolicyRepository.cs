using Microsoft.EntityFrameworkCore; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports; using SmeAccounting.Infrastructure.Persistence;
namespace SmeAccounting.Infrastructure.Repositories;
public class EfInventoryValuationPolicyRepository : IInventoryValuationPolicyRepository
{
    private readonly SmeAccountingDbContext _ctx;
    public EfInventoryValuationPolicyRepository(SmeAccountingDbContext ctx) => _ctx = ctx;
    public Task<InventoryValuationPolicy?> GetByIdAsync(long id) => _ctx.InventoryValuationPolicies.FirstOrDefaultAsync(e => e.Id == id);
    public Task<InventoryValuationPolicy?> GetByCodeAsync(string code, long companyId) => _ctx.InventoryValuationPolicies.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<InventoryValuationPolicy>> GetAllByCompanyAsync(long companyId) => await _ctx.InventoryValuationPolicies.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public Task AddAsync(InventoryValuationPolicy policy) => _ctx.InventoryValuationPolicies.AddAsync(policy).AsTask();
}
