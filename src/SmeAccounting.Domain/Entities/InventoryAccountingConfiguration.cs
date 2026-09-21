using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class InventoryAccountingConfiguration : BaseEntity
{
    public long CompanyId { get; private set; }
    public long InventoryAccountId { get; private set; }
    public long CogsAccountId { get; private set; }
    public long? InventoryAdjustmentGainAccountId { get; private set; }
    public long? InventoryAdjustmentLossAccountId { get; private set; }
    public bool IsActive { get; private set; } = true;

    private InventoryAccountingConfiguration() { }

    public InventoryAccountingConfiguration(long companyId, long inventoryAccountId, long cogsAccountId, long? adjustmentGainAccountId = null, long? adjustmentLossAccountId = null)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (inventoryAccountId <= 0) throw new DomainException("InventoryAccountId must be greater than zero.");
        if (cogsAccountId <= 0) throw new DomainException("CogsAccountId must be greater than zero.");
        if (inventoryAccountId == cogsAccountId) throw new DomainException("Inventory and COGS accounts must differ.");

        CompanyId = companyId;
        InventoryAccountId = inventoryAccountId;
        CogsAccountId = cogsAccountId;
        InventoryAdjustmentGainAccountId = adjustmentGainAccountId;
        InventoryAdjustmentLossAccountId = adjustmentLossAccountId;

        AddDomainEvent(new InventoryAccountingConfigurationCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
