using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IWarehouseRepository
{
    Task<Warehouse?> GetByIdAsync(long id);
    Task<Warehouse?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Warehouse>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Warehouse warehouse);
}
