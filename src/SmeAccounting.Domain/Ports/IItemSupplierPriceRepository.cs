using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemSupplierPriceRepository
{
    Task<ItemSupplierPrice?> GetByIdAsync(long id);
    Task<IReadOnlyList<ItemSupplierPrice>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemSupplierPrice itemSupplierPrice);
}
