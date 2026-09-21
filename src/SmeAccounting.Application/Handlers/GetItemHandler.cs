using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemHandler(IItemRepository repository)
    : IRequestHandler<GetItemQuery, ItemDto?>,
      IRequestHandler<GetItemsByCompanyQuery, IReadOnlyList<ItemDto>>
{
    public async Task<ItemDto?> Handle(GetItemQuery request, CancellationToken cancellationToken)
    {
        var item = await repository.GetByIdAsync(request.Id);
        return item == null ? null : Map(item);
    }

    public async Task<IReadOnlyList<ItemDto>> Handle(GetItemsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var items = await repository.GetAllByCompanyAsync(request.CompanyId);
        return items.Select(Map).ToList();
    }

    private static ItemDto Map(SmeAccounting.Domain.Entities.Item i)
        => new ItemDto(i.Id, i.CompanyId, i.Code, i.Name, i.ItemCategoryId, i.UomId, i.IsStockItem, i.IsServiceItem, i.IsActive, i.Description);
}
