using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxRuleRepository : ITaxRuleRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxRuleRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxRule?> GetByIdAsync(long id)
    {
        return await _context.TaxRules
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxRule?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxRules
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxRule>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxRules
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.TaxTypeId)
            .ThenBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<TaxRule>> GetActiveRulesForDateAsync(DateOnly date, long companyId)
    {
        return await _context.TaxRules
            .AsNoTracking()
            .Where(e =>
                e.CompanyId == companyId &&
                e.EffectiveFrom <= date &&
                (e.EffectiveTo == null || e.EffectiveTo >= date) &&
                e.IsActive)
            .OrderBy(e => e.TaxTypeId)
            .ThenBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxRule taxRule)
    {
        await _context.TaxRules.AddAsync(taxRule);
    }
}
