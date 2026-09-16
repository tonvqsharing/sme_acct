using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfAccountRepository : IAccountRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfAccountRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Account?> GetByIdAsync(long id)
    {
        return await _context.Accounts
            .Include(a => a.Children)
            .FirstOrDefaultAsync(a => a.Id == id);
    }

    public async Task<IReadOnlyList<Account>> GetAllAsync()
    {
        return await _context.Accounts
            .AsNoTracking()
            .OrderBy(a => a.Code.Value)
            .ToListAsync();
    }

    public async Task AddAsync(Account account)
    {
        await _context.Accounts.AddAsync(account);
    }

    public async Task UpdateAsync(Account account)
    {
        _context.Accounts.Update(account);
        await Task.CompletedTask;
    }
}
