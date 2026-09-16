using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCostCenterRepository : ICostCenterRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfCostCenterRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<CostCenter?> GetByIdAsync(long id)
    {
        return await _context.CostCenters
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<CostCenter?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.CostCenters
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<CostCenter>> GetAllAsync()
    {
        return await _context.CostCenters
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(CostCenter costCenter)
    {
        await _context.CostCenters.AddAsync(costCenter);
    }
}
