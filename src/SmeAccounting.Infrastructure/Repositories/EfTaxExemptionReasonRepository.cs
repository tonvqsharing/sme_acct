using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxExemptionReasonRepository : ITaxExemptionReasonRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxExemptionReasonRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxExemptionReason?> GetByIdAsync(long id)
    {
        return await _context.TaxExemptionReasons
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxExemptionReason?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxExemptionReasons
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxExemptionReason>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxExemptionReasons
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<TaxExemptionReason>> GetAllByTaxTypeAsync(long taxTypeId)
    {
        return await _context.TaxExemptionReasons
            .AsNoTracking()
            .Where(e => e.TaxTypeId == taxTypeId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxExemptionReason taxExemptionReason)
    {
        await _context.TaxExemptionReasons.AddAsync(taxExemptionReason);
    }
}
