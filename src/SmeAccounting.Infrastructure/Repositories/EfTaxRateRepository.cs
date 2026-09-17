using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxRateRepository : ITaxRateRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxRateRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxRate?> GetByIdAsync(long id)
    {
        return await _context.TaxRates
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxRate?> GetByTaxTypeAndDateAsync(long taxTypeId, DateOnly date, long companyId)
    {
        return await _context.TaxRates
            .AsNoTracking()
            .FirstOrDefaultAsync(e =>
                e.TaxTypeId == taxTypeId
                && e.CompanyId == companyId
                && e.EffectiveFrom <= date
                && (e.EffectiveTo == null || e.EffectiveTo >= date)
                && e.IsActive);
    }

    public async Task<IReadOnlyList<TaxRate>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxRates
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.TaxTypeId)
            .ThenBy(e => e.EffectiveFrom)
            .ToListAsync();
    }

    public async Task AddAsync(TaxRate taxRate)
    {
        await _context.TaxRates.AddAsync(taxRate);
    }
}
