using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTaxAuthorityRepository : ITaxAuthorityRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTaxAuthorityRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TaxAuthority?> GetByIdAsync(long id)
    {
        return await _context.TaxAuthorities
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TaxAuthority?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TaxAuthorities
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TaxAuthority>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.TaxAuthorities
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TaxAuthority taxAuthority)
    {
        await _context.TaxAuthorities.AddAsync(taxAuthority);
    }
}
