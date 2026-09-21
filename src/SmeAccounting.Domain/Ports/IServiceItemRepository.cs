using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IServiceItemRepository
{
    Task<ServiceItem?> GetByIdAsync(long id);
    Task<ServiceItem?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<ServiceItem>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ServiceItem serviceItem);
}
