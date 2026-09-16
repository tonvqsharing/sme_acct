namespace SmeAccounting.Domain.Entities;

public class PostingReference : BaseEntity
{
    public long JournalEntryId { get; private set; }
    public string SourceType { get; private set; } = string.Empty;
    public long SourceId { get; private set; }

    private PostingReference() { }

    public PostingReference(long journalEntryId, string sourceType, long sourceId)
    {
        JournalEntryId = journalEntryId;
        SourceType = sourceType ?? throw new ArgumentNullException(nameof(sourceType));
        SourceId = sourceId;
    }
}
