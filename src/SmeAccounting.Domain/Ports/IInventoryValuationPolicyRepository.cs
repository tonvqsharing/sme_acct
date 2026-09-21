using SmeAccounting.Domain.Entities;
namespace SmeAccounting.Domain.Ports;
public interface IInventoryValuationPolicyRepository
{
    Task<InventoryValuationPolicy?> GetByIdAsync(long id);
    Task<InventoryValuationPolicy?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<InventoryValuationPolicy>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(InventoryValuationPolicy policy);
}
