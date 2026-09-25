using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemReorderLevelHandler(IItemReorderLevelRepository repository)
    : IRequestHandler<GetItemReorderLevelQuery, ItemReorderLevelDto?>,
      IRequestHandler<GetItemReorderLevelsByCompanyQuery, IReadOnlyList<ItemReorderLevelDto>>
{
    public async Task<ItemReorderLevelDto?> Handle(GetItemReorderLevelQuery request, CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.Id);
        return entity == null ? null : Map(entity);
    }

    public async Task<IReadOnlyList<ItemReorderLevelDto>> Handle(GetItemReorderLevelsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities.Select(Map).ToList();
    }

    private static ItemReorderLevelDto Map(SmeAccounting.Domain.Entities.ItemReorderLevel e)
        => new ItemReorderLevelDto(e.Id, e.CompanyId, e.ItemId, e.WarehouseId, e.MinimumQuantity, e.MaximumQuantity, e.IsActive);
}
