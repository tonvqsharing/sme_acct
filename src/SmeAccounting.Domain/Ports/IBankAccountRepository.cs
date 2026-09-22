using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IBankAccountRepository
{
    Task<BankAccount?> GetByIdAsync(long id);
    Task<BankAccount?> GetByCodeAsync(string code, long bankId, long? bankBranchId);
    Task<IReadOnlyList<BankAccount>> GetAllByBankAsync(long bankId);
    Task<IReadOnlyList<BankAccount>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(BankAccount bankAccount);
}
