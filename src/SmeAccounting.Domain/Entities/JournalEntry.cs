using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class JournalEntry : BaseEntity
{
    public string EntryNumber { get; private set; } = string.Empty;
    public DateTimeOffset Date { get; private set; }
    public long PeriodId { get; private set; }
    public string? Description { get; private set; }
    public string? SourceType { get; private set; }
    public long? SourceId { get; private set; }
    public string? PostedBy { get; private set; }
    public DateTimeOffset? PostedAt { get; private set; }
    public bool IsPosted { get; private set; }

    private readonly List<JournalEntryLine> _lines = [];
    public IReadOnlyCollection<JournalEntryLine> Lines => _lines.AsReadOnly();

    private JournalEntry() { }

    public JournalEntry(string entryNumber, DateTimeOffset date, long periodId, string? description = null)
    {
        EntryNumber = entryNumber ?? throw new ArgumentNullException(nameof(entryNumber));
        Date = date;
        PeriodId = periodId;
        Description = description;
    }

    public void SetSource(string sourceType, long sourceId)
    {
        SourceType = sourceType;
        SourceId = sourceId;
    }

    public JournalEntryLine AddLine(long accountId, Money debit, Money credit, string? description = null)
    {
        if (IsPosted)
            throw new DomainException("Cannot modify a posted journal entry.");

        var line = new JournalEntryLine(Id, accountId, debit, credit, description);
        _lines.Add(line);
        return line;
    }

    public void Post(string postedBy, DateTimeOffset postedAt)
    {
        if (IsPosted)
            throw new DomainException("Journal entry is already posted.");

        ValidateBalance();

        PostedBy = postedBy;
        PostedAt = postedAt;
        IsPosted = true;

        AddDomainEvent(new JournalEntryPosted(Id, postedAt));
    }

    public void ValidateBalance()
    {
        var totalDebit = _lines.Sum(l => l.Debit.Amount);
        var totalCredit = _lines.Sum(l => l.Credit.Amount);

        if (totalDebit != totalCredit)
            throw new InvalidPostingRuleException(
                $"Journal entry {EntryNumber} does not balance. Debit: {totalDebit}, Credit: {totalCredit}.");
    }
}
