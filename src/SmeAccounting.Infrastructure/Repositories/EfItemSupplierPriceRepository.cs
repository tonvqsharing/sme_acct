using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemSupplierPriceRepository : IItemSupplierPriceRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfItemSupplierPriceRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemSupplierPrice?> GetByIdAsync(long id)
    {
        return await _context.ItemSupplierPrices
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<ItemSupplierPrice>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.ItemSupplierPrices
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.SupplierId)
            .ThenBy(e => e.ItemId)
            .ThenBy(e => e.EffectiveFrom)
            .ToListAsync();
    }

    public async Task AddAsync(ItemSupplierPrice itemSupplierPrice)
    {
        await _context.ItemSupplierPrices.AddAsync(itemSupplierPrice);
    }
}
