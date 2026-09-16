using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class JournalEntryLine : BaseEntity
{
    public long EntryId { get; private set; }
    public long AccountId { get; private set; }
    public Money Debit { get; private set; } = Money.Zero;
    public Money Credit { get; private set; } = Money.Zero;
    public string? Description { get; private set; }
    public long? DepartmentId { get; private set; }
    public long? CostCenterId { get; private set; }
    public long? ProjectId { get; private set; }

    private JournalEntryLine() { }

    public JournalEntryLine(
        long entryId,
        long accountId,
        Money debit,
        Money credit,
        string? description = null,
        long? departmentId = null,
        long? costCenterId = null,
        long? projectId = null)
    {
        EntryId = entryId;
        AccountId = accountId;
        Debit = debit ?? throw new ArgumentNullException(nameof(debit));
        Credit = credit ?? throw new ArgumentNullException(nameof(credit));
        Description = description;
        DepartmentId = departmentId;
        CostCenterId = costCenterId;
        ProjectId = projectId;
    }
}
