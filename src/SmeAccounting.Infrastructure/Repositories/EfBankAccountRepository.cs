using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfBankAccountRepository : IBankAccountRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfBankAccountRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<BankAccount?> GetByIdAsync(long id)
    {
        return await _context.BankAccounts
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<BankAccount?> GetByCodeAsync(string code, long bankId, long? bankBranchId)
    {
        return await _context.BankAccounts
            .FirstOrDefaultAsync(e => e.Code == code && e.BankId == bankId && e.BankBranchId == bankBranchId);
    }

    public async Task<IReadOnlyList<BankAccount>> GetAllByBankAsync(long bankId)
    {
        return await _context.BankAccounts
            .AsNoTracking()
            .Where(e => e.BankId == bankId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<BankAccount>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.BankAccounts
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(BankAccount bankAccount)
    {
        await _context.BankAccounts.AddAsync(bankAccount);
    }
}
