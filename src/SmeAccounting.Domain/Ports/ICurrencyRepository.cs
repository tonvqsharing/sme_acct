using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICurrencyRepository
{
    Task<Currency?> GetByIdAsync(long id);
    Task<Currency?> GetByCodeAsync(string code);
    Task<IReadOnlyList<Currency>> GetAllAsync();
    Task AddAsync(Currency currency);
}
