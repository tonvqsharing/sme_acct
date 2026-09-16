using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCompanyRepository : ICompanyRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfCompanyRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Company?> GetByIdAsync(long id)
    {
        return await _context.Companies
            .FirstOrDefaultAsync(c => c.Id == id);
    }

    public async Task<Company?> GetByTaxCodeAsync(string taxCode)
    {
        return await _context.Companies
            .FirstOrDefaultAsync(c => c.TaxCode == taxCode);
    }

    public async Task<IReadOnlyList<Company>> GetAllAsync()
    {
        return await _context.Companies
            .AsNoTracking()
            .OrderBy(c => c.Name)
            .ToListAsync();
    }

    public async Task AddAsync(Company company)
    {
        await _context.Companies.AddAsync(company);
    }
}
