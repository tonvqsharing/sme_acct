namespace SmeAccounting.Domain.Events;
public class InventoryAccountingConfigurationCreated : DomainEvent
{
    public long ConfigurationId { get; }
    public long CompanyId { get; }
    public InventoryAccountingConfigurationCreated(long configurationId, long companyId, DateTimeOffset occurredOn) : base(occurredOn) { ConfigurationId = configurationId; CompanyId = companyId; }
}
