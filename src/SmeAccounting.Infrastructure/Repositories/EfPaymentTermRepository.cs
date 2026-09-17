using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPaymentTermRepository : IPaymentTermRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPaymentTermRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PaymentTerm?> GetByIdAsync(long id)
    {
        return await _context.Set<PaymentTerm>()
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<PaymentTerm?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.Set<PaymentTerm>()
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<PaymentTerm>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.Set<PaymentTerm>()
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(PaymentTerm paymentTerm)
    {
        await _context.Set<PaymentTerm>().AddAsync(paymentTerm);
    }
}
