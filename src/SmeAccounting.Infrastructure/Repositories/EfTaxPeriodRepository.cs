using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxPeriodRepository : ITaxPeriodRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxPeriodRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxPeriod?> GetByIdAsync(long id)
    {
        return await _context.TaxPeriods
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<TaxPeriod>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxPeriods
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.FilingDeadline)
            .ToListAsync();
    }

    public async Task<TaxPeriod?> GetByFiscalPeriodAndTaxTypeAsync(long fiscalPeriodId, long taxTypeId, long companyId)
    {
        return await _context.TaxPeriods
            .FirstOrDefaultAsync(e => e.FiscalPeriodId == fiscalPeriodId
                && e.TaxTypeId == taxTypeId
                && e.CompanyId == companyId);
    }

    public async Task AddAsync(TaxPeriod taxPeriod)
    {
        await _context.TaxPeriods.AddAsync(taxPeriod);
    }
}
