using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class Company : BaseEntity
{
    public string Name { get; private set; } = string.Empty;
    public string TaxCode { get; private set; } = string.Empty;
    public string Address { get; private set; } = string.Empty;
    public string? Phone { get; private set; }
    public string? Email { get; private set; }
    public int FiscalYearStartMonth { get; private set; } = 1;
    public int FiscalYearStartDay { get; private set; } = 1;
    public string FunctionalCurrencyCode { get; private set; } = "VND";
    public bool IsActive { get; private set; } = true;

    private Company() { }

    public Company(
        string name,
        string taxCode,
        string address,
        string? phone = null,
        string? email = null,
        int fiscalYearStartMonth = 1,
        int fiscalYearStartDay = 1,
        string functionalCurrencyCode = "VND")
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");
        if (string.IsNullOrWhiteSpace(taxCode))
            throw new DomainException("TaxCode is required.");
        if (string.IsNullOrWhiteSpace(address))
            throw new DomainException("Address is required.");
        if (string.IsNullOrWhiteSpace(functionalCurrencyCode))
            throw new DomainException("FunctionalCurrencyCode is required.");

        if (fiscalYearStartMonth is < 1 or > 12)
            throw new DomainException("FiscalYearStartMonth must be between 1 and 12.");

        if (fiscalYearStartDay is < 1 or > 28)
            throw new DomainException("FiscalYearStartDay must be between 1 and 28.");

        Name = name;
        TaxCode = taxCode;
        Address = address;
        Phone = phone;
        Email = email;
        FunctionalCurrencyCode = functionalCurrencyCode;
        FiscalYearStartMonth = fiscalYearStartMonth;
        FiscalYearStartDay = fiscalYearStartDay;

        AddDomainEvent(new CompanyCreated(Id, DateTimeOffset.UtcNow));
    }
}
