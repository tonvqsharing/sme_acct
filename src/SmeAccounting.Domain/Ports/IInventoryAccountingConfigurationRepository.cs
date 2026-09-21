using SmeAccounting.Domain.Entities;
namespace SmeAccounting.Domain.Ports;
public interface IInventoryAccountingConfigurationRepository
{
    Task<InventoryAccountingConfiguration?> GetByCompanyAsync(long companyId);
    Task<InventoryAccountingConfiguration?> GetByIdAsync(long id);
    Task AddAsync(InventoryAccountingConfiguration configuration);
}
