using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateCompanySettingHandler(
    ICompanySettingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateCompanySettingCommand, CreateCompanySettingResult>
{
    public async Task<CreateCompanySettingResult> Handle(
        CreateCompanySettingCommand request,
        CancellationToken cancellationToken)
    {
        var companySetting = new CompanySetting(
            request.CompanyId,
            request.LegalRepresentativeName,
            request.LegalRepresentativeTaxId,
            request.ChiefAccountantName,
            request.ChiefAccountantTaxId,
            request.FiscalYearStartMonth,
            request.Currency,
            request.ReportingSettingsJson);

        await repository.AddAsync(companySetting);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateCompanySettingResult(companySetting.Id);
    }
}
