using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemTaxClassRepository
{
    Task<ItemTaxClass?> GetByIdAsync(long id);
    Task<IReadOnlyList<ItemTaxClass>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemTaxClass itemTaxClass);
}