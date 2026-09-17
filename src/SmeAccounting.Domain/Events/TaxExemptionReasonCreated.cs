namespace SmeAccounting.Domain.Events;

public class TaxExemptionReasonCreated : DomainEvent
{
    public long TaxExemptionReasonId { get; }
    public long CompanyId { get; }

    public TaxExemptionReasonCreated(
        long taxExemptionReasonId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxExemptionReasonId = taxExemptionReasonId;
        CompanyId = companyId;
    }
}
