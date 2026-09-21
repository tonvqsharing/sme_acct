using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class OpeningBalanceEntry : BaseEntity
{
    public long OpeningBalancePeriodId { get; private set; }
    public long CompanyId { get; private set; }
    public long AccountId { get; private set; }
    public Money Debit { get; private set; } = Money.Zero;
    public Money Credit { get; private set; } = Money.Zero;
    public string? Description { get; private set; }

    private OpeningBalanceEntry() { }

    public OpeningBalanceEntry(
        long openingBalancePeriodId,
        long companyId,
        long accountId,
        Money debit,
        Money credit,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (accountId <= 0)
            throw new DomainException("AccountId must be greater than zero.");

        if (debit is null)
            throw new DomainException("Debit is required.");
        if (credit is null)
            throw new DomainException("Credit is required.");

        if (debit.Amount < 0 || credit.Amount < 0)
            throw new DomainException("Debit and credit amounts must be non-negative.");

        if (debit.Amount == 0 && credit.Amount == 0)
            throw new DomainException("Debit and credit cannot both be zero.");

        if (debit.Currency != credit.Currency)
            throw new DomainException("Debit and credit currencies must match.");

        OpeningBalancePeriodId = openingBalancePeriodId;
        CompanyId = companyId;
        AccountId = accountId;
        Debit = debit;
        Credit = credit;
        Description = description;

        AddDomainEvent(new OpeningBalanceEntryCreated(Id, companyId, DateTimeOffset.UtcNow));
    }
}
