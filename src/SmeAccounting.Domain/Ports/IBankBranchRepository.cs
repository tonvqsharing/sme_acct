using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IBankBranchRepository
{
    Task<BankBranch?> GetByIdAsync(long id);
    Task<BankBranch?> GetByCodeAsync(string code, long bankId);
    Task<IReadOnlyList<BankBranch>> GetAllByBankAsync(long bankId);
    Task<IReadOnlyList<BankBranch>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(BankBranch bankBranch);
}
