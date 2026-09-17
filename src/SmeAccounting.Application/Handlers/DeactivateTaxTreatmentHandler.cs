using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxTreatmentHandler(
    ITaxTreatmentRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxTreatmentCommand, DeactivateTaxTreatmentResult>
{
    public async Task<DeactivateTaxTreatmentResult> Handle(
        DeactivateTaxTreatmentCommand request,
        CancellationToken cancellationToken)
    {
        var taxTreatment = await repository.GetByIdAsync(request.TaxTreatmentId);
        if (taxTreatment is null)
            throw new InvalidOperationException($"Tax treatment with ID {request.TaxTreatmentId} not found.");

        taxTreatment.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxTreatmentResult();
    }
}
