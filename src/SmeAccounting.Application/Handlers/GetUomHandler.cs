using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetUomHandler(IUomRepository repository)
    : IRequestHandler<GetUomQuery, UomDto?>,
      IRequestHandler<GetUomsByCompanyQuery, IReadOnlyList<UomDto>>
{
    public async Task<UomDto?> Handle(GetUomQuery request, CancellationToken cancellationToken)
    {
        var uom = await repository.GetByIdAsync(request.Id);
        if (uom == null) return null;
        return Map(uom);
    }

    public async Task<IReadOnlyList<UomDto>> Handle(GetUomsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var uoms = await repository.GetAllByCompanyAsync(request.CompanyId);
        return uoms.Select(Map).ToList();
    }

    private static UomDto Map(SmeAccounting.Domain.Entities.Uom u)
        => new UomDto(u.Id, u.CompanyId, u.Code, u.Name, u.Symbol, u.UomClassId, u.IsActive, u.Description);
}
