using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemBarcodeHandler(
    IItemBarcodeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemBarcodeCommand, CreateItemBarcodeResult>
{
    public async Task<CreateItemBarcodeResult> Handle(
        CreateItemBarcodeCommand request,
        CancellationToken cancellationToken)
    {
        var itemBarcode = new ItemBarcode(
            request.CompanyId,
            request.ItemId,
            request.Barcode,
            request.BarcodeType,
            request.UomId,
            request.IsPrimary);

        await repository.AddAsync(itemBarcode);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateItemBarcodeResult(itemBarcode.Id);
    }
}