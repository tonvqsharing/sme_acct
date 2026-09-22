using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class BankAccount : BaseEntity
{
    public long CompanyId { get; private set; }
    public long BankId { get; private set; }
    public long? BankBranchId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string AccountNumber { get; private set; } = string.Empty;
    public string AccountName { get; private set; } = string.Empty;
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }
    public string? CurrencyCode { get; private set; }

    private BankAccount() { }

    public BankAccount(long companyId, long bankId, string code, string accountNumber, string accountName, long? bankBranchId = null, string? description = null, string? currencyCode = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (bankId <= 0)
            throw new DomainException("BankId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(accountNumber))
            throw new DomainException("AccountNumber is required.");
        if (string.IsNullOrWhiteSpace(accountName))
            throw new DomainException("AccountName is required.");

        CompanyId = companyId;
        BankId = bankId;
        BankBranchId = bankBranchId;
        Code = code;
        AccountNumber = accountNumber;
        AccountName = accountName;
        Description = description;
        CurrencyCode = currencyCode;

        AddDomainEvent(new BankAccountCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
