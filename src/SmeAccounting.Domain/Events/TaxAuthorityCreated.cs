namespace SmeAccounting.Domain.Events;

public class TaxAuthorityCreated : DomainEvent
{
    public long TaxAuthorityId { get; }
    public long CompanyId { get; }

    public TaxAuthorityCreated(
        long taxAuthorityId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxAuthorityId = taxAuthorityId;
        CompanyId = companyId;
    }
}
