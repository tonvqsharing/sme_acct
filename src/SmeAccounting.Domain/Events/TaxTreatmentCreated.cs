namespace SmeAccounting.Domain.Events;

public class TaxTreatmentCreated : DomainEvent
{
    public long TaxTreatmentId { get; }
    public long CompanyId { get; }

    public TaxTreatmentCreated(
        long taxTreatmentId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TaxTreatmentId = taxTreatmentId;
        CompanyId = companyId;
    }
}
