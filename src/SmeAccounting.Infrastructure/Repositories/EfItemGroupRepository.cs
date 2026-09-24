using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemGroupRepository : IItemGroupRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfItemGroupRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemGroup?> GetByIdAsync(long id)
    {
        return await _context.ItemGroups
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<ItemGroup?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.ItemGroups
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<ItemGroup>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.ItemGroups
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(ItemGroup itemGroup)
    {
        await _context.ItemGroups.AddAsync(itemGroup);
    }
}