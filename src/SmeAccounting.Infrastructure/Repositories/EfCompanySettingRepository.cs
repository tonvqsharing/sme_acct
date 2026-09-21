using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfCompanySettingRepository : ICompanySettingRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfCompanySettingRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<CompanySetting?> GetByIdAsync(long id)
    {
        return await _context.CompanySettings
            .FirstOrDefaultAsync(s => s.Id == id);
    }

    public async Task<CompanySetting?> GetByCompanyIdAsync(long companyId)
    {
        return await _context.CompanySettings
            .FirstOrDefaultAsync(s => s.CompanyId == companyId);
    }

    public async Task AddAsync(CompanySetting companySetting)
    {
        await _context.CompanySettings.AddAsync(companySetting);
    }
}
