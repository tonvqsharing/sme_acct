using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateCompanySettingCommand(
    long CompanyId,
    string LegalRepresentativeName,
    string LegalRepresentativeTaxId,
    string? ChiefAccountantName = null,
    string? ChiefAccountantTaxId = null,
    int? FiscalYearStartMonth = null,
    string? Currency = null,
    string? ReportingSettingsJson = null) : IRequest<CreateCompanySettingResult>;

public record CreateCompanySettingResult(long Id);
