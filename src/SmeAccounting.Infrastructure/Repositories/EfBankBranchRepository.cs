using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfBankBranchRepository : IBankBranchRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfBankBranchRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<BankBranch?> GetByIdAsync(long id)
    {
        return await _context.BankBranches
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<BankBranch?> GetByCodeAsync(string code, long bankId)
    {
        return await _context.BankBranches
            .FirstOrDefaultAsync(e => e.Code == code && e.BankId == bankId);
    }

    public async Task<IReadOnlyList<BankBranch>> GetAllByBankAsync(long bankId)
    {
        return await _context.BankBranches
            .AsNoTracking()
            .Where(e => e.BankId == bankId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<BankBranch>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.BankBranches
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(BankBranch bankBranch)
    {
        await _context.BankBranches.AddAsync(bankBranch);
    }
}
