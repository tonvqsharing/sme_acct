using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxExemptionReasonHandler(
    ITaxExemptionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxExemptionReasonCommand, CreateTaxExemptionReasonResult>
{
    public async Task<CreateTaxExemptionReasonResult> Handle(
        CreateTaxExemptionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var taxExemptionReason = new TaxExemptionReason(
            request.CompanyId, request.TaxTypeId,
            request.Code, request.Name,
            request.LegalBasis, request.Description);

        await repository.AddAsync(taxExemptionReason);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxExemptionReasonResult(taxExemptionReason.Id);
    }
}
