using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfUomClassRepository : IUomClassRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfUomClassRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<UomClass?> GetByIdAsync(long id)
    {
        return await _context.UomClasses
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<UomClass?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.UomClasses
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<UomClass>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.UomClasses
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(UomClass uomClass)
    {
        await _context.UomClasses.AddAsync(uomClass);
    }
}