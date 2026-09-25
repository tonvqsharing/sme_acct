using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetItemTaxClassHandler(
    IItemTaxClassRepository repository)
    : IRequestHandler<GetItemTaxClassQuery, ItemTaxClassDto?>,
      IRequestHandler<GetItemTaxClassesByCompanyQuery, IReadOnlyList<ItemTaxClassDto>>
{
    public Task<ItemTaxClassDto?> Handle(GetItemTaxClassQuery request, CancellationToken cancellationToken)
        => Task.FromResult(GetByIdInternal(request.Id));

    public Task<IReadOnlyList<ItemTaxClassDto>> Handle(GetItemTaxClassesByCompanyQuery request, CancellationToken cancellationToken)
        => Task.FromResult(GetAllByCompanyInternal(request.CompanyId));

    private static ItemTaxClassDto Map(SmeAccounting.Domain.Entities.ItemTaxClass e)
    {
        return new ItemTaxClassDto(
            e.Id,
            e.CompanyId,
            e.ItemId,
            e.TaxTypeId,
            e.EffectiveFrom,
            e.EffectiveTo,
            e.IsActive);
    }

    private ItemTaxClassDto? GetByIdInternal(long id)
    {
        var entity = repository.GetByIdAsync(id).GetAwaiter().GetResult();
        return entity is null ? null : Map(entity);
    }

    private IReadOnlyList<ItemTaxClassDto> GetAllByCompanyInternal(long companyId)
    {
        var entities = repository.GetAllByCompanyAsync(companyId).GetAwaiter().GetResult();
        return entities.Select(Map).ToList();
    }
}