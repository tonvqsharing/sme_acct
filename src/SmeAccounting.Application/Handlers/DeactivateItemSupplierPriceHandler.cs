using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemSupplierPriceHandler(
    IItemSupplierPriceRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemSupplierPriceCommand, DeactivateItemSupplierPriceResult>
{
    public async Task<DeactivateItemSupplierPriceResult> Handle(
        DeactivateItemSupplierPriceCommand request,
        CancellationToken cancellationToken)
    {
        var itemSupplierPrice = await repository.GetByIdAsync(request.Id);
        if (itemSupplierPrice is null)
            throw new InvalidOperationException($"Item supplier price with ID {request.Id} not found.");

        itemSupplierPrice.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateItemSupplierPriceResult(true);
    }
}
