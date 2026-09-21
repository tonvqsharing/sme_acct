using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class CompanySetting : BaseEntity
{
    public long CompanyId { get; private set; }
    public string LegalRepresentativeName { get; private set; } = string.Empty;
    public string LegalRepresentativeTaxId { get; private set; } = string.Empty;
    public string? ChiefAccountantName { get; private set; }
    public string? ChiefAccountantTaxId { get; private set; }
    public int? FiscalYearStartMonth { get; private set; }
    public string? Currency { get; private set; }
    public string? ReportingSettingsJson { get; private set; }

    private CompanySetting() { }

    public CompanySetting(
        long companyId,
        string legalRepresentativeName,
        string legalRepresentativeTaxId,
        string? chiefAccountantName = null,
        string? chiefAccountantTaxId = null,
        int? fiscalYearStartMonth = null,
        string? currency = null,
        string? reportingSettingsJson = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");

        if (string.IsNullOrWhiteSpace(legalRepresentativeName))
            throw new DomainException("LegalRepresentativeName is required.");

        if (string.IsNullOrWhiteSpace(legalRepresentativeTaxId))
            throw new DomainException("LegalRepresentativeTaxId is required.");

        if (fiscalYearStartMonth is < 1 or > 12)
            throw new DomainException("FiscalYearStartMonth must be between 1 and 12.");

        CompanyId = companyId;
        LegalRepresentativeName = legalRepresentativeName;
        LegalRepresentativeTaxId = legalRepresentativeTaxId;
        ChiefAccountantName = chiefAccountantName;
        ChiefAccountantTaxId = chiefAccountantTaxId;
        FiscalYearStartMonth = fiscalYearStartMonth;
        Currency = currency;
        ReportingSettingsJson = reportingSettingsJson;

        AddDomainEvent(new CompanySettingCreated(Id, companyId, DateTimeOffset.UtcNow));
    }
}
