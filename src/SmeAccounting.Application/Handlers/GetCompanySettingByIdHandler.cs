using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetCompanySettingByIdHandler(
    ICompanySettingRepository repository)
    : IRequestHandler<GetCompanySettingByIdQuery, CompanySettingDto?>
{
    public async Task<CompanySettingDto?> Handle(
        GetCompanySettingByIdQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.Id);
        return entity is null ? null : new CompanySettingDto(
            entity.Id,
            entity.CompanyId,
            entity.LegalRepresentativeName,
            entity.LegalRepresentativeTaxId,
            entity.ChiefAccountantName,
            entity.ChiefAccountantTaxId,
            entity.FiscalYearStartMonth,
            entity.Currency,
            entity.ReportingSettingsJson);
    }
}
