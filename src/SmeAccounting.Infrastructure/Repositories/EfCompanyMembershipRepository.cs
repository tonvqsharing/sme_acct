using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCompanyMembershipRepository : ICompanyMembershipRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfCompanyMembershipRepository(SmeAccountingDbContext context) => _context = context;
    public async Task AddAsync(CompanyMembership membership) => await _context.CompanyMemberships.AddAsync(membership);
}
