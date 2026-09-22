using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfBankRepository : IBankRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfBankRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Bank?> GetByIdAsync(long id)
    {
        return await _context.Banks
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Bank?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Banks
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Bank>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Banks
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Bank bank)
    {
        await _context.Banks.AddAsync(bank);
    }
}
