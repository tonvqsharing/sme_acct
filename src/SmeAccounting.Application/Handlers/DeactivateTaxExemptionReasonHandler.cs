using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxExemptionReasonHandler(
    ITaxExemptionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxExemptionReasonCommand, DeactivateTaxExemptionReasonResult>
{
    public async Task<DeactivateTaxExemptionReasonResult> Handle(
        DeactivateTaxExemptionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var taxExemptionReason = await repository.GetByIdAsync(request.TaxExemptionReasonId);
        if (taxExemptionReason is null)
            throw new InvalidOperationException($"Tax exemption reason with ID {request.TaxExemptionReasonId} not found.");

        taxExemptionReason.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxExemptionReasonResult();
    }
}
