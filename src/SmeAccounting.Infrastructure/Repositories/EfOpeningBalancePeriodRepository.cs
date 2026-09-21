using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfOpeningBalancePeriodRepository : IOpeningBalancePeriodRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfOpeningBalancePeriodRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<OpeningBalancePeriod?> GetByIdAsync(long id)
    {
        return await _context.OpeningBalancePeriods
            .Include(p => p.Entries)
            .FirstOrDefaultAsync(p => p.Id == id);
    }

    public async Task<OpeningBalancePeriod?> GetByCompanyAndFiscalPeriodAsync(long companyId, long fiscalPeriodId)
    {
        return await _context.OpeningBalancePeriods
            .Include(p => p.Entries)
            .FirstOrDefaultAsync(p => p.CompanyId == companyId && p.FiscalPeriodId == fiscalPeriodId);
    }

    public async Task<IReadOnlyList<OpeningBalancePeriod>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.OpeningBalancePeriods
            .AsNoTracking()
            .Where(p => p.CompanyId == companyId)
            .OrderByDescending(p => p.PeriodDate)
            .ToListAsync();
    }

    public async Task AddAsync(OpeningBalancePeriod period)
    {
        await _context.OpeningBalancePeriods.AddAsync(period);
    }
}
