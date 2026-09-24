using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPriceListHandler(IPriceListRepository repository)
    : IRequestHandler<GetPriceListQuery, PriceListDto?>,
      IRequestHandler<GetPriceListsByCompanyQuery, IReadOnlyList<PriceListDto>>
{
    public async Task<PriceListDto?> Handle(GetPriceListQuery request, CancellationToken cancellationToken)
    {
        var priceList = await repository.GetByIdAsync(request.Id);
        if (priceList == null) return null;
        return Map(priceList);
    }

    public async Task<IReadOnlyList<PriceListDto>> Handle(GetPriceListsByCompanyQuery request, CancellationToken cancellationToken)
    {
        var priceLists = await repository.GetAllByCompanyAsync(request.CompanyId);
        return priceLists.Select(Map).ToList();
    }

    private static PriceListDto Map(SmeAccounting.Domain.Entities.PriceList p)
        => new PriceListDto(p.Id, p.CompanyId, p.Code, p.Name, p.IsActive, p.Description);
}