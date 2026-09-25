using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateWarehouseLocationHandler(
    IWarehouseLocationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateWarehouseLocationCommand, DeactivateWarehouseLocationResult>
{
    public async Task<DeactivateWarehouseLocationResult> Handle(DeactivateWarehouseLocationCommand request, CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.Id);
        if (entity is null)
            throw new InvalidOperationException($"WarehouseLocation with ID {request.Id} not found.");

        entity.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateWarehouseLocationResult(true);
    }
}