using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IUsersRepository
{
    Task<User?> GetByIdAsync(long id);
    Task<User?> GetByExternalIdAsync(string externalId);
    Task<User?> GetByEmailAsync(string email);
    Task<IReadOnlyList<User>> GetAllAsync();
    Task AddAsync(User user);
}
