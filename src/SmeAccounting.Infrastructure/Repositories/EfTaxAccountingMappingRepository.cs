using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxAccountingMappingRepository : ITaxAccountingMappingRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxAccountingMappingRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxAccountingMapping?> GetByIdAsync(long id)
    {
        return await _context.TaxAccountingMappings
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<TaxAccountingMapping>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxAccountingMappings
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.MappingType)
            .ToListAsync();
    }

    public async Task<TaxAccountingMapping?> GetByTaxTypeAndTreatmentAsync(long taxTypeId, long taxTreatmentId, long companyId)
    {
        return await _context.TaxAccountingMappings
            .FirstOrDefaultAsync(e => e.TaxTypeId == taxTypeId && e.TaxTreatmentId == taxTreatmentId && e.CompanyId == companyId);
    }

    public async Task AddAsync(TaxAccountingMapping mapping)
    {
        await _context.TaxAccountingMappings.AddAsync(mapping);
    }
}
