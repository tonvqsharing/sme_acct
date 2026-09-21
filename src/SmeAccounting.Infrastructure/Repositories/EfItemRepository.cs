using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemRepository : IItemRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfItemRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Item?> GetByIdAsync(long id) => await _context.Items.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<Item?> GetByCodeAsync(string code, long companyId) => await _context.Items.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<Item>> GetAllByCompanyAsync(long companyId) => await _context.Items.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public async Task AddAsync(Item item) => await _context.Items.AddAsync(item);
}
