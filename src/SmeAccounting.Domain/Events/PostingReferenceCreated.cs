namespace SmeAccounting.Domain.Events;

public class PostingReferenceCreated : DomainEvent
{
    public long PostingReferenceId { get; }
    public long CompanyId { get; }

    public PostingReferenceCreated(
        long postingReferenceId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        PostingReferenceId = postingReferenceId;
        CompanyId = companyId;
    }
}
