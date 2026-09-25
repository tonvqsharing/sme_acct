using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetWarehouseLocationHandler(
    IWarehouseLocationRepository repository)
    : IRequestHandler<GetWarehouseLocationQuery, WarehouseLocationDto?>,
      IRequestHandler<GetWarehouseLocationsByCompanyQuery, IReadOnlyList<WarehouseLocationDto>>
{
    public Task<WarehouseLocationDto?> Handle(GetWarehouseLocationQuery request, CancellationToken cancellationToken)
        => Task.FromResult(GetByIdInternal(request.Id));

    public Task<IReadOnlyList<WarehouseLocationDto>> Handle(GetWarehouseLocationsByCompanyQuery request, CancellationToken cancellationToken)
        => Task.FromResult(GetAllByCompanyInternal(request.CompanyId));

    private static WarehouseLocationDto Map(SmeAccounting.Domain.Entities.WarehouseLocation e)
    {
        return new WarehouseLocationDto(
            e.Id,
            e.CompanyId,
            e.WarehouseId,
            e.Code,
            e.Name,
            e.IsActive,
            e.Description);
    }

    private WarehouseLocationDto? GetByIdInternal(long id)
    {
        var entity = repository.GetByIdAsync(id).GetAwaiter().GetResult();
        return entity is null ? null : Map(entity);
    }

    private IReadOnlyList<WarehouseLocationDto> GetAllByCompanyInternal(long companyId)
    {
        var entities = repository.GetAllByCompanyAsync(companyId).GetAwaiter().GetResult();
        return entities.Select(Map).ToList();
    }
}