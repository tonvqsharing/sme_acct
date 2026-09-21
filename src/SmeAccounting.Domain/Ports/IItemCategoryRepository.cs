using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemCategoryRepository
{
    Task<ItemCategory?> GetByIdAsync(long id);
    Task<ItemCategory?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<ItemCategory>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemCategory category);
}
