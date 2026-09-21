using SmeAccounting.Domain.Entities;
namespace SmeAccounting.Domain.Ports;
public interface IInventoryAdjustmentReasonRepository
{
    Task<InventoryAdjustmentReason?> GetByIdAsync(long id);
    Task<InventoryAdjustmentReason?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<InventoryAdjustmentReason>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(InventoryAdjustmentReason reason);
}
