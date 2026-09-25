using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemReorderLevelRepository : IItemReorderLevelRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfItemReorderLevelRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemReorderLevel?> GetByIdAsync(long id) => await _context.ItemReorderLevels.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<IReadOnlyList<ItemReorderLevel>> GetAllByCompanyAsync(long companyId) => await _context.ItemReorderLevels.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.ItemId).ToListAsync();
    public async Task AddAsync(ItemReorderLevel itemReorderLevel) => await _context.ItemReorderLevels.AddAsync(itemReorderLevel);
}
