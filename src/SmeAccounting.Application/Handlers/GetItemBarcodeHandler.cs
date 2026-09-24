using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemBarcodeHandler(IItemBarcodeRepository repository)
    : IRequestHandler<GetItemBarcodeQuery, ItemBarcodeDto?>,
      IRequestHandler<GetItemBarcodesByCompanyQuery, IReadOnlyList<ItemBarcodeDto>>
{
    public async Task<ItemBarcodeDto?> Handle(GetItemBarcodeQuery request, CancellationToken cancellationToken)
    {
        var itemBarcode = await repository.GetByIdAsync(request.Id);
        return itemBarcode == null ? null : Map(itemBarcode);
    }

    public async Task<IReadOnlyList<ItemBarcodeDto>> Handle(GetItemBarcodesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var itemBarcodes = await repository.GetAllByCompanyAsync(request.CompanyId);
        return itemBarcodes.Select(Map).ToList();
    }

    private static ItemBarcodeDto Map(ItemBarcode b)
        => new ItemBarcodeDto(b.Id, b.CompanyId, b.ItemId, b.Barcode, b.BarcodeType.ToString(), b.UomId, b.IsPrimary, b.IsActive);
}