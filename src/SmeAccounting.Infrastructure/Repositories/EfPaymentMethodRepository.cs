using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPaymentMethodRepository : IPaymentMethodRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPaymentMethodRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PaymentMethod?> GetByIdAsync(long id)
    {
        return await _context.Set<PaymentMethod>()
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<PaymentMethod?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Set<PaymentMethod>()
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<PaymentMethod>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Set<PaymentMethod>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(PaymentMethod paymentMethod)
    {
        await _context.Set<PaymentMethod>().AddAsync(paymentMethod);
    }
}
