using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class PostingReference : BaseEntity
{
    public long CompanyId { get; private set; }
    public long JournalEntryId { get; private set; }
    public string SourceType { get; private set; } = string.Empty;
    public long SourceId { get; private set; }

    private PostingReference() { }

    public PostingReference(long companyId, long journalEntryId, string sourceType, long sourceId)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (journalEntryId <= 0)
            throw new DomainException("JournalEntryId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(sourceType))
            throw new DomainException("SourceType is required.");
        if (sourceId <= 0)
            throw new DomainException("SourceId must be greater than zero.");

        CompanyId = companyId;
        JournalEntryId = journalEntryId;
        SourceType = sourceType;
        SourceId = sourceId;

        AddDomainEvent(new PostingReferenceCreated(Id, companyId, DateTimeOffset.UtcNow));
    }
}
