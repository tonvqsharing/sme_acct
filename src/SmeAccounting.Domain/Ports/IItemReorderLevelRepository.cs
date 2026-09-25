using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemReorderLevelRepository
{
    Task<ItemReorderLevel?> GetByIdAsync(long id);
    Task<IReadOnlyList<ItemReorderLevel>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemReorderLevel itemReorderLevel);
}
