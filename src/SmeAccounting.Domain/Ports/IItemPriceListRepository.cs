using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemPriceListRepository
{
    Task<ItemPriceList?> GetByIdAsync(long id);
    Task<IReadOnlyList<ItemPriceList>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemPriceList itemPriceList);
}