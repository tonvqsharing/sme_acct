using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemSupplierPriceHandler(IItemSupplierPriceRepository repository)
    : IRequestHandler<GetItemSupplierPriceQuery, ItemSupplierPriceDto?>,
      IRequestHandler<GetItemSupplierPricesByCompanyQuery, IReadOnlyList<ItemSupplierPriceDto>>
{
    public async Task<ItemSupplierPriceDto?> Handle(GetItemSupplierPriceQuery request, CancellationToken cancellationToken)
    {
        var itemSupplierPrice = await repository.GetByIdAsync(request.Id);
        if (itemSupplierPrice == null) return null;
        return Map(itemSupplierPrice);
    }

    public async Task<IReadOnlyList<ItemSupplierPriceDto>> Handle(GetItemSupplierPricesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var itemSupplierPrices = await repository.GetAllByCompanyAsync(request.CompanyId);
        return itemSupplierPrices.Select(Map).ToList();
    }

    private static ItemSupplierPriceDto Map(SmeAccounting.Domain.Entities.ItemSupplierPrice p)
        => new ItemSupplierPriceDto(p.Id, p.CompanyId, p.SupplierId, p.ItemId, p.UnitPrice, p.CurrencyCode, p.EffectiveFrom, p.EffectiveTo, p.IsActive);
}
