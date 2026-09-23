using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class OpeningBalancePeriod : BaseEntity
{
    public long CompanyId { get; private set; }
    public long FiscalPeriodId { get; private set; }
    public DateOnly PeriodDate { get; private set; }
    public PeriodStatus Status { get; private set; } = PeriodStatus.Open;
    public bool IsPosted { get; private set; }

    private readonly List<OpeningBalanceEntry> _entries = [];
    public IReadOnlyCollection<OpeningBalanceEntry> Entries => _entries.AsReadOnly();

    private OpeningBalancePeriod() { }

    public OpeningBalancePeriod(long companyId, long fiscalPeriodId, DateOnly periodDate)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (fiscalPeriodId <= 0)
            throw new DomainException("FiscalPeriodId must be greater than zero.");

        CompanyId = companyId;
        FiscalPeriodId = fiscalPeriodId;
        PeriodDate = periodDate;

        AddDomainEvent(new OpeningBalancePeriodCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public OpeningBalanceEntry AddEntry(long accountId, Money debit, Money credit, string? description = null)
    {
        if (IsPosted)
            throw new DomainException("Cannot add entries to a posted opening balance period.");

        if (Status != PeriodStatus.Open)
            throw new DomainException("Cannot add entries to a closed opening balance period.");

        if (accountId <= 0)
            throw new DomainException("AccountId must be greater than zero.");

        if (debit.Amount < 0 || credit.Amount < 0)
            throw new DomainException("Debit and credit amounts must be non-negative.");

        if (debit.Amount == 0 && credit.Amount == 0)
            throw new DomainException("Debit and credit cannot both be zero.");

        if (_entries.Any(e => e.AccountId == accountId))
            throw new DomainException("An entry for this account already exists in the period.");

        var entry = new OpeningBalanceEntry(Id, CompanyId, accountId, debit, credit, description);
        _entries.Add(entry);
        return entry;
    }

    public JournalEntry PostOpeningBalances(string postedBy, DateTimeOffset postedAt)
    {
        if (IsPosted)
            throw new DomainException("Opening balances are already posted.");

        if (Status != PeriodStatus.Open)
            throw new DomainException("Opening balance period is not open.");

        if (!_entries.Any())
            throw new DomainException("No opening balance entries to post.");

        var totalDebit = _entries.Sum(e => e.Debit.Amount);
        var totalCredit = _entries.Sum(e => e.Credit.Amount);

        if (totalDebit != totalCredit)
            throw new DomainException($"Opening balances do not balance. Debit: {totalDebit}, Credit: {totalCredit}.");

        if (Id <= 0)
            throw new DomainException("Cannot post opening balances before the period is persisted.");

        var entryNumber = $"OP-{PeriodDate:yyyyMMdd}";
        var journalEntry = new JournalEntry(entryNumber, postedAt, FiscalPeriodId, $"Opening balances for period {PeriodDate:yyyy-MM-dd}");
        journalEntry.SetSource("OpeningBalance", Id);

        foreach (var entry in _entries)
        {
            journalEntry.AddLine(entry.AccountId, entry.Debit, entry.Credit, entry.Description);
        }

        journalEntry.Post(postedBy, postedAt);

        IsPosted = true;
        Status = PeriodStatus.Closed;

        AddDomainEvent(new OpeningBalancesPosted(Id, CompanyId, DateTimeOffset.UtcNow));

        return journalEntry;
    }
}
