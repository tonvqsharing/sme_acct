using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCurrencyRepository : ICurrencyRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfCurrencyRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Currency?> GetByIdAsync(long id)
    {
        return await _context.Currencies
            .FirstOrDefaultAsync(c => c.Id == id);
    }

    public async Task<Currency?> GetByCodeAsync(string code)
    {
        return await _context.Currencies
            .FirstOrDefaultAsync(c => c.Code == code);
    }

    public async Task<IReadOnlyList<Currency>> GetAllAsync()
    {
        return await _context.Currencies
            .AsNoTracking()
            .OrderBy(c => c.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Currency currency)
    {
        await _context.Currencies.AddAsync(currency);
    }
}
