namespace SmeAccounting.Application.DTOs;

public record CompanySettingDto(
    long Id,
    long CompanyId,
    string LegalRepresentativeName,
    string LegalRepresentativeTaxId,
    string? ChiefAccountantName,
    string? ChiefAccountantTaxId,
    int? FiscalYearStartMonth,
    string? Currency,
    string? ReportingSettingsJson);
