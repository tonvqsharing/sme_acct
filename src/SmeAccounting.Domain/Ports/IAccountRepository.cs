using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IAccountRepository
{
    Task<Account?> GetByIdAsync(long id);
    Task<IReadOnlyList<Account>> GetAllAsync();
    Task AddAsync(Account account);
    Task UpdateAsync(Account account);
}
