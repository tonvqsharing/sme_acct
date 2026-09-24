using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemPriceListRepository : IItemPriceListRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfItemPriceListRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemPriceList?> GetByIdAsync(long id)
    {
        return await _context.ItemPriceLists
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<ItemPriceList>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.ItemPriceLists
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.PriceListId)
            .ThenBy(e => e.ItemId)
            .ThenBy(e => e.EffectiveFrom)
            .ToListAsync();
    }

    public async Task AddAsync(ItemPriceList itemPriceList)
    {
        await _context.ItemPriceLists.AddAsync(itemPriceList);
    }
}