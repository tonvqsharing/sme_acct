using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfUomRepository : IUomRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfUomRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Uom?> GetByIdAsync(long id)
    {
        return await _context.Uoms
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Uom?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Uoms
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Uom>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Uoms
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Uom uom)
    {
        await _context.Uoms.AddAsync(uom);
    }
}
