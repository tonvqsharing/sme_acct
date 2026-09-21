using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemRepository
{
    Task<Item?> GetByIdAsync(long id);
    Task<Item?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Item>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Item item);
}
