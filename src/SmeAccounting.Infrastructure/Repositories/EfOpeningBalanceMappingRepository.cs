using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfOpeningBalanceMappingRepository : IOpeningBalanceMappingRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfOpeningBalanceMappingRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<OpeningBalanceMapping?> GetByIdAsync(long id)
    {
        return await _context.OpeningBalanceMappings
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<OpeningBalanceMapping>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.OpeningBalanceMappings
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.VoucherTypeId)
            .ThenBy(e => e.DebitAccountId)
            .ToListAsync();
    }

    public async Task AddAsync(OpeningBalanceMapping mapping)
    {
        await _context.OpeningBalanceMappings.AddAsync(mapping);
    }
}
