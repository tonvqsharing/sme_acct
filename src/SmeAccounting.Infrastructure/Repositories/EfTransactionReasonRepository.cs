using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTransactionReasonRepository : ITransactionReasonRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTransactionReasonRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TransactionReason?> GetByIdAsync(long id)
    {
        return await _context.TransactionReasons
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TransactionReason?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TransactionReasons
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TransactionReason>> GetAllByVoucherTypeAsync(long voucherTypeId)
    {
        return await _context.TransactionReasons
            .AsNoTracking()
            .Where(e => e.VoucherTypeId == voucherTypeId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TransactionReason transactionReason)
    {
        await _context.TransactionReasons.AddAsync(transactionReason);
    }
}
