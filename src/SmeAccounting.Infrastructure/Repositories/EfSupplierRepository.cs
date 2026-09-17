using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfSupplierRepository : ISupplierRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfSupplierRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Supplier?> GetByIdAsync(long id)
    {
        return await _context.Set<Supplier>()
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Supplier?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Set<Supplier>()
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Supplier>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Set<Supplier>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Supplier supplier)
    {
        await _context.Set<Supplier>().AddAsync(supplier);
    }
}
