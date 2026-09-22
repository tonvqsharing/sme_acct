using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IBankRepository
{
    Task<Bank?> GetByIdAsync(long id);
    Task<Bank?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Bank>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Bank bank);
}
