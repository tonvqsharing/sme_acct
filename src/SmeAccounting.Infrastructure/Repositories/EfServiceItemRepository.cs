using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfServiceItemRepository : IServiceItemRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfServiceItemRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ServiceItem?> GetByIdAsync(long id) => await _context.ServiceItems.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<ServiceItem?> GetByCodeAsync(string code, long companyId) => await _context.ServiceItems.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<ServiceItem>> GetAllByCompanyAsync(long companyId) => await _context.ServiceItems.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public async Task AddAsync(ServiceItem serviceItem) => await _context.ServiceItems.AddAsync(serviceItem);
}
