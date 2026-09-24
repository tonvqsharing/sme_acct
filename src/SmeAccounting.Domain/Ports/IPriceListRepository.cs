using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPriceListRepository
{
    Task<PriceList?> GetByIdAsync(long id);
    Task<PriceList?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<PriceList>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PriceList priceList);
}