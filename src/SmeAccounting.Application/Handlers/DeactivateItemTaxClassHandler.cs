using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemTaxClassHandler(
    IItemTaxClassRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemTaxClassCommand, DeactivateItemTaxClassResult>
{
    public async Task<DeactivateItemTaxClassResult> Handle(DeactivateItemTaxClassCommand request, CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.Id);
        if (entity is null)
            throw new InvalidOperationException($"ItemTaxClass with ID {request.Id} not found.");

        entity.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateItemTaxClassResult(true);
    }
}