using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxRateHandler(
    ITaxRateRepository repository)
    : IRequestHandler<GetTaxRateQuery, TaxRateDto?>
{
    public async Task<TaxRateDto?> Handle(
        GetTaxRateQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxRateId);
        return entity is null ? null : new TaxRateDto(
            entity.Id, entity.CompanyId, entity.TaxTypeId,
            entity.RateValue, entity.RateName,
            entity.EffectiveFrom, entity.EffectiveTo,
            entity.IsActive, entity.Description);
    }
}
