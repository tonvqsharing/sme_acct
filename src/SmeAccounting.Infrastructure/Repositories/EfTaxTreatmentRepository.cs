using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxTreatmentRepository : ITaxTreatmentRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxTreatmentRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxTreatment?> GetByIdAsync(long id)
    {
        return await _context.TaxTreatments
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxTreatment?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxTreatments
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxTreatment>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxTreatments
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<TaxTreatment>> GetAllByTaxTypeAsync(long taxTypeId)
    {
        return await _context.TaxTreatments
            .AsNoTracking()
            .Where(e => e.TaxTypeId == taxTypeId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxTreatment taxTreatment)
    {
        await _context.TaxTreatments.AddAsync(taxTreatment);
    }
}
