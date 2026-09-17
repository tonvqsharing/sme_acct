using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxTreatmentHandler(
    ITaxTreatmentRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxTreatmentCommand, CreateTaxTreatmentResult>
{
    public async Task<CreateTaxTreatmentResult> Handle(
        CreateTaxTreatmentCommand request,
        CancellationToken cancellationToken)
    {
        var taxTreatment = new TaxTreatment(
            request.CompanyId, request.TaxTypeId,
            request.Code, request.Name,
            request.TaxTreatmentType, request.InputCreditAllowed,
            request.Description);

        await repository.AddAsync(taxTreatment);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxTreatmentResult(taxTreatment.Id);
    }
}
