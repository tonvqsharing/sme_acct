using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfEmployeeRepository : IEmployeeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfEmployeeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Employee?> GetByIdAsync(long id)
    {
        return await _context.Set<Employee>()
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Employee?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Set<Employee>()
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<Employee?> GetByEmployeeNumberAsync(string employeeNumber, long companyId)
    {
        return await _context.Set<Employee>()
            .FirstOrDefaultAsync(e => e.EmployeeNumber == employeeNumber && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Employee>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Set<Employee>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Employee employee)
    {
        await _context.Set<Employee>().AddAsync(employee);
    }
}
