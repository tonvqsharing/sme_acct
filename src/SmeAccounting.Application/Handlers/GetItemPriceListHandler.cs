using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemPriceListHandler(IItemPriceListRepository repository)
    : IRequestHandler<GetItemPriceListQuery, ItemPriceListDto?>,
      IRequestHandler<GetItemPriceListsByCompanyQuery, IReadOnlyList<ItemPriceListDto>>
{
    public async Task<ItemPriceListDto?> Handle(GetItemPriceListQuery request, CancellationToken cancellationToken)
    {
        var itemPriceList = await repository.GetByIdAsync(request.Id);
        if (itemPriceList == null) return null;
        return Map(itemPriceList);
    }

    public async Task<IReadOnlyList<ItemPriceListDto>> Handle(GetItemPriceListsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var itemPriceLists = await repository.GetAllByCompanyAsync(request.CompanyId);
        return itemPriceLists.Select(Map).ToList();
    }

    private static ItemPriceListDto Map(SmeAccounting.Domain.Entities.ItemPriceList p)
        => new ItemPriceListDto(p.Id, p.CompanyId, p.PriceListId, p.ItemId, p.UnitPrice, p.CurrencyCode, p.EffectiveFrom, p.EffectiveTo, p.IsActive);
}