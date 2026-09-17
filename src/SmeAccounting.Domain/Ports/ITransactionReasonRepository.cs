using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITransactionReasonRepository
{
    Task<TransactionReason?> GetByIdAsync(long id);
    Task<TransactionReason?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TransactionReason>> GetAllByVoucherTypeAsync(long voucherTypeId);
    Task AddAsync(TransactionReason transactionReason);
}
