using SmeAccounting.Domain.Events;

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
        Name = name ?? throw new ArgumentNullException(nameof(name));
        TaxCode = taxCode ?? throw new ArgumentNullException(nameof(taxCode));
        Address = address ?? throw new ArgumentNullException(nameof(address));
        Phone = phone;
        Email = email;
        FunctionalCurrencyCode = functionalCurrencyCode ?? throw new ArgumentNullException(nameof(functionalCurrencyCode));

        if (fiscalYearStartMonth is < 1 or > 12)
            throw new ArgumentOutOfRangeException(nameof(fiscalYearStartMonth), "Fiscal year start month must be between 1 and 12.");

        if (fiscalYearStartDay is < 1 or > 28)
            throw new ArgumentOutOfRangeException(nameof(fiscalYearStartDay), "Fiscal year start day must be between 1 and 28.");

        FiscalYearStartMonth = fiscalYearStartMonth;
        FiscalYearStartDay = fiscalYearStartDay;

        AddDomainEvent(new CompanyCreated(Id, DateTimeOffset.UtcNow));
    }
}
