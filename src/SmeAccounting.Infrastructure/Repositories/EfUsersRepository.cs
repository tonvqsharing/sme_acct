using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfUsersRepository : IUsersRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfUsersRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<User?> GetByIdAsync(long id)
    {
        return await _context.Users.FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<User?> GetByExternalIdAsync(string externalId)
    {
        return await _context.Users.FirstOrDefaultAsync(u => u.ExternalId == externalId);
    }

    public async Task<User?> GetByEmailAsync(string email)
    {
        return await _context.Users.FirstOrDefaultAsync(u => u.Email == email.ToLowerInvariant());
    }

    public async Task<IReadOnlyList<User>> GetAllAsync()
    {
        return await _context.Users.AsNoTracking().ToListAsync();
    }

    public async Task AddAsync(User user)
    {
        await _context.Users.AddAsync(user);
    }
}
