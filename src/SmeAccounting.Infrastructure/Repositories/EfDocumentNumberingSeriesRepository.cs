using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfDocumentNumberingSeriesRepository : IDocumentNumberingSeriesRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfDocumentNumberingSeriesRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<DocumentNumberingSeries?> GetByIdAsync(long id)
    {
        return await _context.DocumentNumberingSeries
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId)
    {
        return await _context.DocumentNumberingSeries
            .FirstOrDefaultAsync(e => e.VoucherTypeId == voucherTypeId
                && e.CompanyId == companyId && e.IsDefault);
    }

    public async Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.DocumentNumberingSeries
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Prefix)
            .ToListAsync();
    }

    public async Task AddAsync(DocumentNumberingSeries series)
    {
        await _context.DocumentNumberingSeries.AddAsync(series);
    }
}
