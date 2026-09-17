using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCustomerRepository : ICustomerRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfCustomerRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Customer?> GetByIdAsync(long id)
    {
        return await _context.Set<Customer>()
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Customer?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Set<Customer>()
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Customer>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Set<Customer>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Customer customer)
    {
        await _context.Set<Customer>().AddAsync(customer);
    }
}
