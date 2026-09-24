using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemBarcodeHandler(
    IItemBarcodeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemBarcodeCommand, DeactivateItemBarcodeResult>
{
    public async Task<DeactivateItemBarcodeResult> Handle(
        DeactivateItemBarcodeCommand request,
        CancellationToken cancellationToken)
    {
        var itemBarcode = await repository.GetByIdAsync(request.Id);
        if (itemBarcode is null)
            throw new InvalidOperationException($"Item barcode with ID {request.Id} not found.");

        itemBarcode.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateItemBarcodeResult(true);
    }
}