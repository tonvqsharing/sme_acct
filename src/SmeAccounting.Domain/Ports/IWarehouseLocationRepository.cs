using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IWarehouseLocationRepository
{
    Task<WarehouseLocation?> GetByIdAsync(long id);
    Task<WarehouseLocation?> GetByCodeAsync(string code, long companyId, long warehouseId);
    Task<IReadOnlyList<WarehouseLocation>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(WarehouseLocation warehouseLocation);
}