namespace SmeAccounting.Domain.Events;
public class InventoryValuationPolicyCreated : DomainEvent
{
    public long PolicyId { get; }
    public long CompanyId { get; }
    public InventoryValuationPolicyCreated(long policyId, long companyId, DateTimeOffset occurredOn) : base(occurredOn) { PolicyId = policyId; CompanyId = companyId; }
}
