namespace SmeAccounting.Domain.Events;

public class OpeningBalanceEntryCreated : DomainEvent
{
    public long EntryId { get; }
    public long CompanyId { get; }

    public OpeningBalanceEntryCreated(long entryId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        EntryId = entryId;
        CompanyId = companyId;
    }
}
