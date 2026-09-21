using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfUomConversionRepository : IUomConversionRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfUomConversionRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<UomConversion?> GetByIdAsync(long id) => await _context.UomConversions.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<IReadOnlyList<UomConversion>> GetByCompanyAsync(long companyId) => await _context.UomConversions.AsNoTracking().Where(e => e.CompanyId == companyId).ToListAsync();
    public async Task AddAsync(UomConversion conversion) => await _context.UomConversions.AddAsync(conversion);
}
