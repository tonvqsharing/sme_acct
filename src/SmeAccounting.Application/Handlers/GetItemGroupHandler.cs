using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemGroupHandler(IItemGroupRepository repository)
    : IRequestHandler<GetItemGroupQuery, ItemGroupDto?>,
      IRequestHandler<GetItemGroupsByCompanyQuery, IReadOnlyList<ItemGroupDto>>
{
    public async Task<ItemGroupDto?> Handle(GetItemGroupQuery request, CancellationToken cancellationToken)
    {
        var itemGroup = await repository.GetByIdAsync(request.Id);
        if (itemGroup == null) return null;
        return Map(itemGroup);
    }

    public async Task<IReadOnlyList<ItemGroupDto>> Handle(GetItemGroupsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var itemGroups = await repository.GetAllByCompanyAsync(request.CompanyId);
        return itemGroups.Select(Map).ToList();
    }

    private static ItemGroupDto Map(SmeAccounting.Domain.Entities.ItemGroup g)
        => new ItemGroupDto(g.Id, g.CompanyId, g.Code, g.Name, g.IsActive, g.Description);
}