using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICostCenterRepository
{
    Task<CostCenter?> GetByIdAsync(long id);
    Task<CostCenter?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<CostCenter>> GetAllAsync();
    Task AddAsync(CostCenter costCenter);
}
