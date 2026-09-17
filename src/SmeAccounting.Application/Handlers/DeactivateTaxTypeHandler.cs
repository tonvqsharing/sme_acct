using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxTypeHandler(
    ITaxTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxTypeCommand, DeactivateTaxTypeResult>
{
    public async Task<DeactivateTaxTypeResult> Handle(
        DeactivateTaxTypeCommand request,
        CancellationToken cancellationToken)
    {
        var taxType = await repository.GetByIdAsync(request.TaxTypeId);
        if (taxType is null)
            throw new InvalidOperationException($"Tax type with ID {request.TaxTypeId} not found.");

        taxType.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxTypeResult();
    }
}
