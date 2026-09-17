using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxPeriodHandler(
    ITaxPeriodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxPeriodCommand, CreateTaxPeriodResult>
{
    public async Task<CreateTaxPeriodResult> Handle(
        CreateTaxPeriodCommand request,
        CancellationToken cancellationToken)
    {
        var taxPeriod = new TaxPeriod(
            request.CompanyId, request.FiscalPeriodId,
            request.TaxTypeId, request.FilingFrequency,
            request.FilingDeadline, request.Description);

        await repository.AddAsync(taxPeriod);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxPeriodResult(taxPeriod.Id);
    }
}
