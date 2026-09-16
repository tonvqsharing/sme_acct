using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Domain.ValueObjects;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfExchangeRateRepository : IExchangeRateRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfExchangeRateRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ExchangeRate?> GetByIdAsync(long id)
    {
        return await _context.ExchangeRates
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<ExchangeRate?> GetByCurrencyPairAsync(
        string fromCurrencyCode,
        string toCurrencyCode,
        ExchangeRateType rateType,
        DateOnly effectiveDate)
    {
        return await _context.ExchangeRates
            .FirstOrDefaultAsync(e =>
                e.FromCurrencyCode == fromCurrencyCode.ToUpperInvariant() &&
                e.ToCurrencyCode == toCurrencyCode.ToUpperInvariant() &&
                e.RateType == rateType &&
                e.EffectiveDate == effectiveDate);
    }

    public async Task<IReadOnlyList<ExchangeRate>> GetAllAsync()
    {
        return await _context.ExchangeRates
            .AsNoTracking()
            .OrderBy(e => e.EffectiveDate)
            .ThenBy(e => e.FromCurrencyCode)
            .ToListAsync();
    }

    public async Task AddAsync(ExchangeRate exchangeRate)
    {
        await _context.ExchangeRates.AddAsync(exchangeRate);
    }
}
