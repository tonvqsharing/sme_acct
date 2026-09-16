using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfVoucherTypeRepository : IVoucherTypeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfVoucherTypeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<VoucherType?> GetByIdAsync(long id)
    {
        return await _context.VoucherTypes
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<VoucherType?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.VoucherTypes
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<VoucherType>> GetAllAsync()
    {
        return await _context.VoucherTypes
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(VoucherType voucherType)
    {
        await _context.VoucherTypes.AddAsync(voucherType);
    }
}
