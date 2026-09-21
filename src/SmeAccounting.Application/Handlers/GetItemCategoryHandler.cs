using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemCategoryHandler(IItemCategoryRepository repository)
    : IRequestHandler<GetItemCategoryQuery, ItemCategoryDto?>,
      IRequestHandler<GetItemCategoriesByCompanyQuery, IReadOnlyList<ItemCategoryDto>>
{
    public async Task<ItemCategoryDto?> Handle(GetItemCategoryQuery request, CancellationToken cancellationToken)
    {
        var cat = await repository.GetByIdAsync(request.Id);
        return cat == null ? null : Map(cat);
    }

    public async Task<IReadOnlyList<ItemCategoryDto>> Handle(GetItemCategoriesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var cats = await repository.GetAllByCompanyAsync(request.CompanyId);
        return cats.Select(Map).ToList();
    }

    private static ItemCategoryDto Map(SmeAccounting.Domain.Entities.ItemCategory c)
        => new ItemCategoryDto(c.Id, c.CompanyId, c.Code, c.Name, c.ParentId, c.IsActive, c.Description);
}
