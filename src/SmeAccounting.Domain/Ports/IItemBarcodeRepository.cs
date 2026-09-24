using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemBarcodeRepository
{
    Task<ItemBarcode?> GetByIdAsync(long id);
    Task<IReadOnlyList<ItemBarcode>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemBarcode itemBarcode);
}