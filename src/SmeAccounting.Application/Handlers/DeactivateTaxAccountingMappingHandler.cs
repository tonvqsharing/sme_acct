using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxAccountingMappingHandler(
    ITaxAccountingMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxAccountingMappingCommand, DeactivateTaxAccountingMappingResult>
{
    public async Task<DeactivateTaxAccountingMappingResult> Handle(
        DeactivateTaxAccountingMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = await repository.GetByIdAsync(request.TaxAccountingMappingId);
        if (mapping is null)
            throw new InvalidOperationException($"Tax accounting mapping with ID {request.TaxAccountingMappingId} not found.");

        mapping.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxAccountingMappingResult();
    }
}
