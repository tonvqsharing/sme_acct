using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxTypeRepository : ITaxTypeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxTypeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxType?> GetByIdAsync(long id)
    {
        return await _context.TaxTypes
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxType?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxTypes
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxType>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxTypes
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxType taxType)
    {
        await _context.TaxTypes.AddAsync(taxType);
    }
}
