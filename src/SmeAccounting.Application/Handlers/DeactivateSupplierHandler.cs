using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateSupplierHandler(
    ISupplierRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateSupplierCommand, DeactivateSupplierResult>
{
    public async Task<DeactivateSupplierResult> Handle(
        DeactivateSupplierCommand request,
        CancellationToken cancellationToken)
    {
        var supplier = await repository.GetByIdAsync(request.SupplierId);
        if (supplier is null)
            throw new InvalidOperationException($"Supplier with ID {request.SupplierId} not found.");

        supplier.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateSupplierResult();
    }
}
