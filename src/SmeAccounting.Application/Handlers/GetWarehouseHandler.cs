using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetWarehouseHandler(IWarehouseRepository repository)
    : IRequestHandler<GetWarehouseQuery, WarehouseDto?>,
      IRequestHandler<GetWarehousesByCompanyQuery, IReadOnlyList<WarehouseDto>>
{
    public async Task<WarehouseDto?> Handle(GetWarehouseQuery request, CancellationToken cancellationToken)
    {
        var wh = await repository.GetByIdAsync(request.Id);
        return wh == null ? null : Map(wh);
    }

    public async Task<IReadOnlyList<WarehouseDto>> Handle(GetWarehousesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var whs = await repository.GetAllByCompanyAsync(request.CompanyId);
        return whs.Select(Map).ToList();
    }

    private static WarehouseDto Map(SmeAccounting.Domain.Entities.Warehouse w)
        => new WarehouseDto(w.Id, w.CompanyId, w.Code, w.Name, w.Address, w.IsActive, w.Description);
}
