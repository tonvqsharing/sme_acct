using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxRatesByCompanyHandler(
    ITaxRateRepository repository)
    : IRequestHandler<GetTaxRatesByCompanyQuery, IReadOnlyList<TaxRateDto>>
{
    public async Task<IReadOnlyList<TaxRateDto>> Handle(
        GetTaxRatesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxRateDto(
                e.Id, e.CompanyId, e.TaxTypeId,
                e.RateValue, e.RateName,
                e.EffectiveFrom, e.EffectiveTo,
                e.IsActive, e.Description))
            .ToList();
    }
}
