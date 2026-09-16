namespace SmeAccounting.Domain.Events;

public class JournalEntryPosted : DomainEvent
{
    public long EntryId { get; }

    public JournalEntryPosted(long entryId, DateTimeOffset occurredOn) : base(occurredOn)
    {
        EntryId = entryId;
    }
}
