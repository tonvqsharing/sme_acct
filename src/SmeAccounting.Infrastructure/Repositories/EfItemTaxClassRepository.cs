using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

internal sealed class EfItemTaxClassRepository : IItemTaxClassRepository
{
    private readonly SmeAccountingDbContext _dbContext;

    public EfItemTaxClassRepository(SmeAccountingDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<ItemTaxClass?> GetByIdAsync(long id)
    {
        return await _dbContext.Set<ItemTaxClass>().FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<ItemTaxClass>> GetAllByCompanyAsync(long companyId)
    {
        return await _dbContext.Set<ItemTaxClass>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.ItemId)
            .ThenBy(e => e.EffectiveFrom)
            .ToListAsync();
    }

    public async Task AddAsync(ItemTaxClass itemTaxClass)
    {
        await _dbContext.Set<ItemTaxClass>().AddAsync(itemTaxClass);
    }
}