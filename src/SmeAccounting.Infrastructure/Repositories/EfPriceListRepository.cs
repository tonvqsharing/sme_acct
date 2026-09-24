using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPriceListRepository : IPriceListRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPriceListRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PriceList?> GetByIdAsync(long id)
    {
        return await _context.PriceLists
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<PriceList?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.PriceLists
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<PriceList>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.PriceLists
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(PriceList priceList)
    {
        await _context.PriceLists.AddAsync(priceList);
    }
}