using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetUomClassHandler(IUomClassRepository repository)
    : IRequestHandler<GetUomClassQuery, UomClassDto?>,
      IRequestHandler<GetUomClassesByCompanyQuery, IReadOnlyList<UomClassDto>>
{
    public async Task<UomClassDto?> Handle(GetUomClassQuery request, CancellationToken cancellationToken)
    {
        var uomClass = await repository.GetByIdAsync(request.Id);
        if (uomClass == null) return null;
        return Map(uomClass);
    }

    public async Task<IReadOnlyList<UomClassDto>> Handle(GetUomClassesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var uomClasses = await repository.GetAllByCompanyAsync(request.CompanyId);
        return uomClasses.Select(Map).ToList();
    }

    private static UomClassDto Map(SmeAccounting.Domain.Entities.UomClass u)
        => new UomClassDto(u.Id, u.CompanyId, u.Code, u.Name, u.IsActive, u.Description);
}