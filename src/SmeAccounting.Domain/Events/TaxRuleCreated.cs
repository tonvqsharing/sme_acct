namespace SmeAccounting.Domain.Events;

public class TaxRuleCreated : DomainEvent
{
    public long TaxRuleId { get; }
    public long CompanyId { get; }

    public TaxRuleCreated(
        long taxRuleId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxRuleId = taxRuleId;
        CompanyId = companyId;
    }
}
