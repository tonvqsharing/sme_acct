using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfUserRoleRepository : IUserRoleRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfUserRoleRepository(SmeAccountingDbContext context) => _context = context;
    public async Task AddAsync(UserRole userRole) => await _context.UserRoles.AddAsync(userRole);
}
