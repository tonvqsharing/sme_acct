using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemCategoryRepository : IItemCategoryRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfItemCategoryRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemCategory?> GetByIdAsync(long id) => await _context.ItemCategories.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<ItemCategory?> GetByCodeAsync(string code, long companyId) => await _context.ItemCategories.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<ItemCategory>> GetAllByCompanyAsync(long companyId) => await _context.ItemCategories.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public async Task AddAsync(ItemCategory category) => await _context.ItemCategories.AddAsync(category);
}
