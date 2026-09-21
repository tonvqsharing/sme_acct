using Microsoft.EntityFrameworkCore; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports; using SmeAccounting.Infrastructure.Persistence;
namespace SmeAccounting.Infrastructure.Repositories;
public class EfInventoryAdjustmentReasonRepository : IInventoryAdjustmentReasonRepository
{
    private readonly SmeAccountingDbContext _ctx;
    public EfInventoryAdjustmentReasonRepository(SmeAccountingDbContext ctx) => _ctx = ctx;
    public Task<InventoryAdjustmentReason?> GetByIdAsync(long id) => _ctx.InventoryAdjustmentReasons.FirstOrDefaultAsync(e => e.Id == id);
    public Task<InventoryAdjustmentReason?> GetByCodeAsync(string code, long companyId) => _ctx.InventoryAdjustmentReasons.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<InventoryAdjustmentReason>> GetAllByCompanyAsync(long companyId) => await _ctx.InventoryAdjustmentReasons.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public Task AddAsync(InventoryAdjustmentReason reason) => _ctx.InventoryAdjustmentReasons.AddAsync(reason).AsTask();
}
