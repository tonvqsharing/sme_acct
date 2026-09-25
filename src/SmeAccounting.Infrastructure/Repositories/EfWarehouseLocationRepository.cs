using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

internal sealed class EfWarehouseLocationRepository : IWarehouseLocationRepository
{
    private readonly SmeAccountingDbContext _dbContext;

    public EfWarehouseLocationRepository(SmeAccountingDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<WarehouseLocation?> GetByIdAsync(long id)
    {
        return await _dbContext.Set<WarehouseLocation>().FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<WarehouseLocation?> GetByCodeAsync(string code, long companyId, long warehouseId)
    {
        return await _dbContext.Set<WarehouseLocation>()
            .FirstOrDefaultAsync(e => e.CompanyId == companyId && e.WarehouseId == warehouseId && e.Code == code);
    }

    public async Task<IReadOnlyList<WarehouseLocation>> GetAllByCompanyAsync(long companyId)
    {
        return await _dbContext.Set<WarehouseLocation>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.WarehouseId)
            .ThenBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(WarehouseLocation warehouseLocation)
    {
        await _dbContext.Set<WarehouseLocation>().AddAsync(warehouseLocation);
    }
}