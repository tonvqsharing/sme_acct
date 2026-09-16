using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfProjectRepository : IProjectRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfProjectRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Project?> GetByIdAsync(long id)
    {
        return await _context.Projects
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<Project?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Projects
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<Project>> GetAllAsync()
    {
        return await _context.Projects
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(Project project)
    {
        await _context.Projects.AddAsync(project);
    }
}
