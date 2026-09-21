using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetUomConversionHandler(IUomConversionRepository repository)
    : IRequestHandler<GetUomConversionQuery, UomConversionDto?>,
      IRequestHandler<GetUomConversionsByCompanyQuery, IReadOnlyList<UomConversionDto>>
{
    public async Task<UomConversionDto?> Handle(GetUomConversionQuery request, CancellationToken cancellationToken)
    {
        var conv = await repository.GetByIdAsync(request.Id);
        return conv == null ? null : Map(conv);
    }

    public async Task<IReadOnlyList<UomConversionDto>> Handle(GetUomConversionsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var convs = await repository.GetByCompanyAsync(request.CompanyId);
        return convs.Select(Map).ToList();
    }

    private static UomConversionDto Map(SmeAccounting.Domain.Entities.UomConversion c)
        => new UomConversionDto(c.Id, c.CompanyId, c.FromUomId, c.ToUomId, c.Factor, c.IsActive);
}
