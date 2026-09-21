using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfOpeningBalanceEntryRepository : IOpeningBalanceEntryRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfOpeningBalanceEntryRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<OpeningBalanceEntry?> GetByIdAsync(long id)
    {
        return await _context.OpeningBalanceEntries
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<OpeningBalanceEntry>> GetAllByPeriodAsync(long periodId)
    {
        return await _context.OpeningBalanceEntries
            .AsNoTracking()
            .Where(e => e.OpeningBalancePeriodId == periodId)
            .OrderBy(e => e.AccountId)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<OpeningBalanceEntry>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.OpeningBalanceEntries
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.OpeningBalancePeriodId)
            .ThenBy(e => e.AccountId)
            .ToListAsync();
    }

    public async Task AddAsync(OpeningBalanceEntry entry)
    {
        await _context.OpeningBalanceEntries.AddAsync(entry);
    }
}
