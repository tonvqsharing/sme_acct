using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateWarehouseHandler(
    IWarehouseRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateWarehouseCommand, DeactivateWarehouseResult>
{
    public async Task<DeactivateWarehouseResult> Handle(DeactivateWarehouseCommand request, CancellationToken cancellationToken)
    {
        var wh = await repository.GetByIdAsync(request.Id);
        if (wh == null) return new DeactivateWarehouseResult(false);
        wh.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateWarehouseResult(true);
    }
}
