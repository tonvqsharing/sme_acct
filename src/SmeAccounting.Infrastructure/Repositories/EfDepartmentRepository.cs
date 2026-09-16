using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfDepartmentRepository : IDepartmentRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfDepartmentRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Department?> GetByIdAsync(long id)
    {
        return await _context.Departments
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Department?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Departments
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Department>> GetAllAsync()
    {
        return await _context.Departments
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Department department)
    {
        await _context.Departments.AddAsync(department);
    }
}
