using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfRoleRepository : IRoleRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfRoleRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Role?> GetByIdAsync(long id)
    {
        return await _context.Roles.FirstOrDefaultAsync(r => r.Id == id);
    }

    public async Task<Role?> GetByCompanyAndCodeAsync(long companyId, string code)
    {
        return await _context.Roles.FirstOrDefaultAsync(r => r.CompanyId == companyId && r.Code == code);
    }

    public async Task<IReadOnlyList<Role>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Roles.AsNoTracking()
            .Where(r => r.CompanyId == companyId)
            .OrderBy(r => r.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Role role)
    {
        await _context.Roles.AddAsync(role);
    }
}
